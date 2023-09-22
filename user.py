class User:
  def __init__(self, 
               email, 
               id, 
               passwd, 
               accessToken=None,
               refreshToken=None):
    self.email = email
    self.id = id
    self.passwd = passwd
    self.access_T = accessToken
    self.refresh_T = refreshToken
    self.commands = []


def serializeUser(usr: User):
  return {
    'email': usr.email,
    'id': usr.id,
    'access_T': usr.access_T,
    'refresh_T': usr.refresh_T,
  }

def getUserCommands(usr: User):
  return usr.commands
