# Reading exercise. Have a look at the code below and tell us:

# 1. What do you think the code is doing?
# 2. What do you like / dislike about the code?
# 3. What would you change?

import subprocess, os, tempfile
from flask import Flask, request, jsonify
import functools
import jwt

AUTH_HEADER_NAME = 'Authorization'

SSH_CERT_VALIDITY = "+5m"

AUTH_AUDIENCE = os.environ.get("F7T_AUTH_TOKEN_AUD", '').strip('\'"')
AUTH_REQUIRED_SCOPE = os.environ.get("F7T_AUTH_REQUIRED_SCOPE", '').strip('\'"')

AUTH_ROLE = os.environ.get("F7T_AUTH_ROLE", '').strip('\'"')

PORT = os.environ.get("F7T_PORT", 5000)

realm_pubkey=os.environ.get("F7T_REALM_RSA_PUBLIC_KEY", '')
if realm_pubkey != '':
    # headers are inserted here, must not be present
    realm_pubkey = realm_pubkey.strip('\'"')   # remove '"'
    realm_pubkey = '-----BEGIN PUBLIC KEY-----\n' + realm_pubkey + '\n-----END PUBLIC KEY-----'
    realm_pubkey_type = os.environ.get("F7T_REALM_RSA_TYPE").strip('\'"')

debug = os.environ.get("F7T_DEBUG_MODE", False)

app = Flask(__name__)


def check_header(header):

    # header = "Bearer ey...", remove first 7 chars
    try:
        decoded = jwt.decode(header[7:], verify=False)

        if AUTH_REQUIRED_SCOPE != "":
            if AUTH_REQUIRED_SCOPE not in decoded["scope"].split():
                return False

        return True

    except jwt.exceptions.InvalidSignatureError:
        app.logger.error("JWT invalid signature", exc_info=True)
    except jwt.ExpiredSignatureError:
        app.logger.error("JWT token has expired", exc_info=True)
    except jwt.InvalidAudienceError:
        app.logger.error("JWT token invalid audience", exc_info=True)
    except jwt.exceptions.InvalidAlgorithmError:
        app.logger.error("JWT invalid signature algorithm", exc_info=True)
    except Exception:
        app.logger.error("Bad header or JWT, general exception raised", exc_info=True)

    return False

# receive the header, and extract the username from the token
# returns username
def get_username(header):
    if debug:
        app.logger.info('debug: cscs_api_common: get_username: ' + header)
    # header = "Bearer ey...", remove first 7 chars
    try:
        if realm_pubkey == '':
            decoded = jwt.decode(header[7:], verify=False)
        else:
            decoded = jwt.decode(header[7:], realm_pubkey, algorithms=realm_pubkey_type, options={'verify_aud': False})

        try:
            if AUTH_ROLE in decoded["realm_access"]["roles"]:

                clientId = decoded["clientId"]
                username = decoded["resource_access"][clientId]["roles"][0]
                return username
            return decoded['preferred_username']
        except Exception:
            return decoded['preferred_username']

    except jwt.exceptions.InvalidSignatureError:
        app.logger.error("JWT invalid signature", exc_info=True)
    except jwt.ExpiredSignatureError:
        app.logger.error("JWT token has expired", exc_info=True)
    except jwt.InvalidAudienceError:
        app.logger.error("JWT token invalid audience", exc_info=True)
    except jwt.exceptions.InvalidAlgorithmError:
        app.logger.error("JWT invalid signature algorithm", exc_info=True)
    except Exception:
        app.logger.error("Bad header or JWT, general exception raised", exc_info=True)

    return None

def check_auth_header(func):
    @functools.wraps(func)
    def wrapper_check_auth_header(*args, **kwargs):
        try:
            auth_header = request.headers[AUTH_HEADER_NAME]
        except KeyError:
            app.logger.error("No Auth Header given")
            return jsonify(description="No Auth Header given"), 401
        if not check_header(auth_header):
            return jsonify(description="Invalid header"), 401

        return func(*args, **kwargs)
    return wrapper_check_auth_header

@app.route("/", methods=["GET"])
@check_auth_header
def receive():

    try:
        auth_header = request.headers[AUTH_HEADER_NAME]
        username = get_username(auth_header)
        if username == None:
            app.logger.error("No username")
            return jsonify(description="Invalid user"), 401


        system = request.args.get("system","")
        if not system:
            return jsonify(description='No system specified'), 404

        td = tempfile.mkdtemp(prefix = "cert")
        os.symlink(os.getcwd() + "/user-key.pub", td + "/user-key.pub")  # link on temp dir

        command = "ssh-keygen -s ca-key -n {} -V {} -I ca-key {}/user-key.pub ".format(username, SSH_CERT_VALIDITY, td)

        app.logger.info("SSH keygen command: {}".format(command))

    except Exception as e:
        app.logger.error(e)
        return jsonify(description="Error creating certificate: {}".format(e), error=-1), 404

    try:
        result = subprocess.check_output([command], shell=True)
        with open(td + '/user-key-cert.pub', 'r') as cert_file:
            cert = cert_file.read()

        os.remove(td + "/user-key-cert.pub")
        os.remove(td + "/user-key.pub")
        os.rmdir(td)

        # return certificate
        return jsonify(certificate=cert), 200
    except subprocess.CalledProcessError as e:
        return jsonify(description=e.output, error=e.returncode), 404
    except Exception as e:
        return jsonify(description="Error creating certificate: {}".format(e), error=-1), 404



if __name__ == "__main__":

    app.run(debug=debug, host='0.0.0.0', port=PORT)


