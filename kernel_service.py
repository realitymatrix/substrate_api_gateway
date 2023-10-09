from json import dumps
import logging
import os, time
import requests
import websocket
import queue
from api import createCommand, runCommand
from threading import Thread
from uuid import uuid4
from tornado.escape import json_decode, json_encode, utf8

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 120))

# websocket.enableTrace(True)
class KernelClient():
    
    DEAD_MSG_ID = "deadbeefdeadbeefdeadbeefdeadbeef"
    POST_IDLE_TIMEOUT = 0.5
    DEFAULT_INTERRUPT_WAIT = 1

    def __init__(self, http_api_endpoint, ws_api_endpoint, kernel_id, timeout=REQUEST_TIMEOUT, logger=None):
        self.response_reader = Thread(target=self._read_responses)
        self.http_api_endpoint = http_api_endpoint
        self.kernel_http_api_endpoint = f"{http_api_endpoint}/{kernel_id}"
        self.ws_api_endpoint = ws_api_endpoint
        self.kernel_ws_api_endpoint = f"{ws_api_endpoint}/{kernel_id}/channels"
        self.shutting_down = False
        self.restarting = False
        self.kernel_id = kernel_id
        self.kernel_socket = None
        self.log = logger
        self.log.debug(f"Initializing kernel client ({kernel_id}) to {self.kernel_ws_api_endpoint}")
        self.response_queues = {}
        self.access_token = '6bafd350a7f67d09249ecab3ed25e07d5d6eef3f597e898d'
        try:
            self.kernel_socket = websocket.create_connection(
                f"{ws_api_endpoint}/{kernel_id}/channels?token={self.access_token}", timeout=timeout, enable_multithread=True
            )
        except Exception as e:
            self.log.error(e)
            self.shutdown()
            raise e
        # startup reader thread
        self.response_reader.start()
    
    def shutdown(self):
        """Shut down the client."""
        # Terminate thread, close socket and clear queues.
        self.shutting_down = True

        if self.kernel_socket:
            self.kernel_socket.close()
            self.kernel_socket = None

        if self.response_queues:
            self.response_queues.clear()
            self.response_queues = None

        if self.response_reader:
            self.response_reader.join(timeout=2.0)
            if self.response_reader.is_alive():
                self.log.warning("Response reader thread is not terminated, continuing...")
            self.response_reader = None

        url = f"{self.http_api_endpoint}/{self.kernel_id}?token={self.access_token}"
        response = requests.delete(url, timeout=60)
        if response.status_code == 204:
            self.log.info(f"Kernel {self.kernel_id} shutdown")
            return True
        else:
            msg = f"Error shutting down kernel {self.kernel_id}: {response.content}"
            raise RuntimeError(msg)
    
    def execute(self, code, timeout=REQUEST_TIMEOUT):
        """
        Executes the code provided and returns the result of that execution.
        """
        response = []
        has_error = False
        try:
            msg_id = self._send_request(code)

            post_idle = False
            while True:
                response_message = self._get_response(msg_id, timeout, post_idle)
                if response_message:
                    response_message_type = response_message["msg_type"]

                    if response_message_type == "error" or (
                        response_message_type == "execute_reply"
                        and response_message["content"]["status"] == "error"
                    ):
                        has_error = True
                        response.append(
                            "{}:{}:{}".format(
                                response_message["content"]["ename"],
                                response_message["content"]["evalue"],
                                response_message["content"]["traceback"],
                            )
                        )
                    elif response_message_type == "stream":
                        response.append(
                            KernelClient._convert_raw_response(response_message["content"]["text"])
                        )

                    elif (
                        response_message_type == "execute_result"
                        or response_message_type == "display_data"
                    ):
                        if "text/plain" in response_message["content"]["data"]:
                            response.append(
                                KernelClient._convert_raw_response(
                                    response_message["content"]["data"]["text/plain"]
                                )
                            )
                        elif "text/html" in response_message["content"]["data"]:
                            response.append(
                                KernelClient._convert_raw_response(
                                    response_message["content"]["data"]["text/html"]
                                )
                            )
                    elif response_message_type == "status":
                        if response_message["content"]["execution_state"] == "idle":
                            post_idle = True  # indicate we're at the logical end and timeout poll for next message
                            continue
                    else:
                        self.log.debug(
                            "Unhandled response for msg_id: {} of msg_type: {}".format(
                                msg_id, response_message_type
                            )
                        )

                if (
                    response_message is None
                ):  # We timed out.  If post idle, its ok, else make mention of it
                    if not post_idle:
                        self.log.warning(
                            "Unexpected timeout occurred for msg_id: {} - no 'idle' status received!".format(
                                msg_id
                            )
                        )
                    break

        except Exception as e:
            self.log.debug(e)

        return "".join(response), has_error
    
    def _send_request(self, code):
        """
        Builds the request and submits it to the kernel.  Prior to sending the request it
        creates an empty response queue and adds it to the dictionary using msg_id as the
        key.  The msg_id is returned in order to read responses.
        """
        msg_id = uuid4().hex
        message = KernelClient.__create_execute_request(msg_id, code)

        # create response-queue and add to map for this msg_id
        self.response_queues[msg_id] = queue.Queue()

        self.kernel_socket.send(message)

        return msg_id

    def _get_response(self, msg_id, timeout, post_idle):
        """
        Pulls the next response message from the queue corresponding to msg_id.  If post_idle is true,
        the timeout parameter is set to a very short value since a majority of time, there won't be a
        message in the queue.  However, in cases where a race condition occurs between the idle status
        and the execute_result payload - where the two are out of order, then this will pickup the result.
        """

        if post_idle and timeout > KernelClient.POST_IDLE_TIMEOUT:
            timeout = (
                KernelClient.POST_IDLE_TIMEOUT
            )  # overwrite timeout to small value following idle messages.

        msg_queue = self.response_queues.get(msg_id)
        try:
            self.log.debug(f"Getting response for msg_id: {msg_id} with timeout: {timeout}")
            response = msg_queue.get(timeout=timeout)
            self.log.debug(
                "Got response for msg_id: {}, msg_type: {}".format(
                    msg_id, response["msg_type"] if response else "null"
                )
            )
        except queue.Empty:
            response = None

        return response

    def _read_responses(self):
        """
        Reads responses from the websocket.  For each response read, it is added to the response queue based
        on the messages parent_header.msg_id.  It does this for the duration of the class's lifetime until its
        shutdown method is called, at which time the socket is closed (unblocking the reader) and the thread
        terminates.  If shutdown happens to occur while processing a response (unlikely), termination takes
        place via the loop control boolean.
        """
        try:
            while not self.shutting_down:
                try:
                    raw_message = self.kernel_socket.recv()
                    response_message = json_decode(utf8(raw_message))

                    msg_id = KernelClient._get_msg_id(response_message, self.log)

                    if msg_id not in self.response_queues:
                        # this will happen when the msg_id is generated by the server
                        self.response_queues[msg_id] = queue.Queue()

                    # insert into queue
                    self.log.debug(
                        "Inserting response for msg_id: {}, msg_type: {}".format(
                            msg_id, response_message["msg_type"]
                        )
                    )
                    self.response_queues.get(msg_id).put_nowait(response_message)
                except BaseException as be1:
                    if (
                        self.restarting
                    ):  # If restarting, wait until restart has completed - which includes new socket
                        i = 1
                        while self.restarting:
                            if i >= 10 and i % 2 == 0:
                                self.log.debug(f"Still restarting after {i} secs...")
                            time.sleep(1)
                            i += 1
                        continue
                    raise be1

        except websocket.WebSocketConnectionClosedException:
            pass  # websocket closure most likely due to shutdown

        except BaseException as be2:
            if not self.shutting_down:
                self.log.warning(f"Unexpected exception encountered ({be2})")

        self.log.debug("Response reader thread exiting...")

    @staticmethod
    def _get_msg_id(message, logger):
        msg_id = KernelClient.DEAD_MSG_ID
        if message:
            if "msg_id" in message["parent_header"] and message["parent_header"]["msg_id"]:
                msg_id = message["parent_header"]["msg_id"]
            elif "msg_id" in message:
                # msg_id may not be in the parent_header, see if present in response
                # IPython kernel appears to do this after restarts with a 'starting' status
                msg_id = message["msg_id"]
        else:  # Dump the "dead" message...
            logger.debug(f"+++++ Dumping dead message: {message}")
        return msg_id

    @staticmethod
    def _convert_raw_response(raw_response_message):
        result = raw_response_message
        if isinstance(raw_response_message, str) and "u'" in raw_response_message:
            result = raw_response_message.replace("u'", "")[:-1]

        return result

    @staticmethod
    def __create_execute_request(msg_id, code):
        return json_encode(
            {
                "header": {
                    "username": "",
                    "version": "5.0",
                    "session": "",
                    "msg_id": msg_id,
                    "msg_type": "execute_request",
                },
                "parent_header": {},
                "channel": "shell",
                "content": {
                    "code": "".join(code),
                    "silent": False,
                    "store_history": False,
                    "user_expressions": {},
                    "allow_stdin": False,
                },
                "metadata": {},
                "buffers": {},
            }
        )

def createKernel(user: str):
    post_to_kernels = createCommand(user, 'api/kernels', 'post')
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Bearer {user["access_T"]}'
    }
    body = {
        'commandId': post_to_kernels,
        'userId': user['id']
    }
    run_res = requests.post(
        headers=headers,
        data=dumps(body),
        url='http://localhost:3333/commands/runCommand'
    )
    if not run_res.ok:
        return f'status: {run_res.status_code} ' + f'There was an internal error. {run_res.text}'
    
    response = run_res.json()
    print(response['result']['data']['id'])
    return response['result']['data']['id']


def createWebsocket(kernel_id: str):
    log = logging.getLogger('KernelClient')
    http_api_endpoint = 'http://localhost:8888/api/kernels'
    ws_api_endpoint = 'ws://localhost:8888/api/kernels'
    return KernelClient(
        http_api_endpoint,
        ws_api_endpoint,
        kernel_id,
        timeout=60,
        logger=log
    )
