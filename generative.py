from json import dumps
from pygments import highlight
from pygments.styles import get_all_styles
from pygments.formatters import HtmlFormatter
from pygments.lexers import Python3Lexer

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

def new_user_row(email: str, id: str):
    return f"""
    <tr id="user_row">
        <td>{email[10:]}</td>
        <td>{id}</td>
        <td>
            <button hx-delete="/delete/{id}"
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
                    hx-post="/command/{id}" 
                    hx-target="#user_row" 
                    hx-swap="afterend" 
                    hx-include="closest tr"
                    class="btn btn-primary">
                Add
            </button>
        </td>
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