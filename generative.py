from json import dumps
from pygments import highlight
from pygments.styles import get_all_styles
from pygments.formatters import HtmlFormatter
from pygments.lexers import Python3Lexer
from user import User, serializeUser
import websocket

def new_registration():
    return """
    <form hx-post="/submit" hx-swap="beforeend" hx-target="#new-user" class="mb-3">
        <input type="text" value="peterkorolev95@gmail.com" placeholder="User Name" name="email" class="form-control mb-3"/>
        <input type="text" value="password" placeholder="Password" name="password" class="form-control mb-3" />
        <button hx-post="/submit" class="btn btn-primary">
            Submit
        </button>
    </button>
    </form>
"""

def new_user_row(usr: User):
    user = serializeUser(usr)
    user_JSON = dumps(user)
    return f"""
    <tr id="user_row">
        <form>
            <td>{usr.email[10:]}</td>
            <td>{usr.id}</td>
            <td>
                <button hx-delete="/delete/{usr.id}"
                    class="btn btn-primary">
                    Delete User
                </button>
            </td>
            <td width="wrap">
                    Command
                    <label>Type</label>
                    <select 
                            name="typec" 
                            hx-target="#add"
                            hx-indicator=".htmx-indicator">
                        <option value="get">GET</option>
                        <option value="post">POST</option>
                        <option value="put">PUT</option>
                        <option value="patch">PATCH</option>
                        <option value="delete">DELETE</option>
                    </select>
                    <textarea
                        id="command"
                        name="command" 
                        type="text" 
                        placeholder="Command"
                        class="form-control mb-3"></textarea>
            </td>
            <td>
                <button id="add" 
                        hx-post="/command/{usr.id}"
                        hx-vals='{{ "user": {user_JSON} }}' 
                        hx-target="#user_row" 
                        hx-swap="afterend" 
                        hx-include="closest tr"
                        class="btn btn-primary">
                    Add
                </button>
            </td>
            <td id="createkernel" >
                <button hx-post="/kernel" 
                        hx-vals='{{ "user": {user_JSON} }}' 
                        hx-target="#createkernel"
                        hx-swap="outerHTML" 
                        hx-include="closest tr"
                        class="btn btn-primary">
                    Create Kernel
                </button>
            </td>
        </form>
    </tr>
        """

def new_command_row(command: str, type: str, command_id: str, usr: str):
    usr = dumps(usr)
    return f"""
    <tr id="command_row">
        <form>
            <td width="wrap">
                <label>{type.upper()}</label>
                <textarea type="text" readonly name="command_text" class="form-control mb-3">{command}</textarea>
            </td>
            <td>{command_id}</td>
            <td>
                <button hx-post="/execute/{command_id}" 
                        hx-vals='{{ "user": {usr} }}'
                        hx-target="#result"
                        hx-swap="afterend" 
                        class="btn btn-primary">
                    Send
                </button>
                <button hx-delete="/command/delete/{command_id}" 
                        hx-target="#command_row" 
                        hx-vals='{{ "user": {usr} }}'
                        class="btn btn-primary">
                    Delete
                </button>
            </td>
            <td id="result"></td>
        </form>
    </tr>
"""

def command_response(response_text: str):
    # formatter = HtmlFormatter(style='default')
    # style_definitions = formatter.get_style_defs()
    # style_bg_color = formatter.style.background_color
    # highlighted_code = highlight(response_text, Python3Lexer(), formatter)
    lines = response_text.split('\n')
    max_cols = max([len(line) for line in lines])
    newlines = response_text.count('\n') + 1
    return f"""
    <td>
        <textarea class="code" rows="{newlines}" cols={max_cols} readonly>{response_text}</textarea>
    </td>
"""

def open_websocket_connection(kernel_id: str):
    return f"""
        <td id="connect_websocket">
            <button hx-post="/websocket/open/{kernel_id}"
                    hx-target="#connect_websocket"
                    hx-swap="outerHTML"
                    class="btn btn-primary">
                Open Websocket
            </button>
        </td>
    """

def close_websocket_connection(kernel_id: str):
    return f"""
        <td>
            <form>
                <textarea id="ws_textarea" wrap="soft" cols="25" rows="2" name="ws_text" type="text" name="command_ws" class="code"></textarea>
            <form>
            <button hx-post="/websocket/run/{kernel_id}"
                    hx-target="#ws_textarea"
                    hx-include="closest form"
                    hx-swap="afterend"
                    class="btn btn-primary">
                Send
            </button>
            <button id="disconnect_websocket" 
                    hx-delete="/websocket/close/{kernel_id}"
                    hx-target="closest td"
                    hx-include="closest form"
                    hx-swap="outerHTML"
                    hx-vals='{{ "kernel_id": {kernel_id} }}'
                    class="btn btn-primary">
                Close Websocket
            </button>
            <button hx-target="#ws-response" 
                    hx-swap="delete" 
                    class="btn btn-primary">Clear Messages</button>
        </td>
    """

def write_response(ws_response: str):
    lines = ws_response.split('\n')
    max_cols = max([len(line) for line in lines])
    newlines = ws_response.count('\n') + 1
    print(max_cols)
    print(newlines)
    return f"""
    <textarea class="code"
              id="ws-response"
              cols="{max_cols}"
              rows={newlines}
              readonly 
              name="ws_res">{ws_response}</textarea>
"""