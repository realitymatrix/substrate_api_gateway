
def new_user_row(email: str, id: str):
    return f"""
    <tr>
        <td>{email[10:]}</td>
        <td>{id}</td>
        <td>
            <button hx-delete="/delete/{id}"
                class="btn btn-primary">
                Delete User
            </button>
        </td>
        <td width="wrap">
            <form>
                Command
                <label>Type</label>
                <select name="command_type" hx-indicator=".htmx-indicator">
                    <option value="get">GET</option>
                    <option value="post">POST</option>
                    <option value="put">PUT</option>
                    <option value="patch">PATCH</option>
                    <option value="delete">DELETE</option>
                </select>
                <textarea type="text" placeholder="Command" name="command_text" class="form-control mb-3"></textarea>
            </form>
        </td>
        <td>
            <button hx-post="/command/{id}" class="btn btn-primary">
                Add
            </button>
        </td>
    </tr>
        """

def new_command_row(command: str, type: str):
    return f"""
    <tr>
        <td width="wrap">
            <label>{type}</label>
            <textarea type="text" readonly name="command" class="form-control mb-3">{command}</textarea>
        </td>
        <td></td>
        <td>
            <button hx-post="/execute/{id}" class="btn btn-primary">
                Send
            </button>
            <button hx-post="/delete_command/{id}" class="btn btn-primary">
                Delete
            </button>
        </td>
    </tr>
"""