#
#  Copyright (c) 2019-2021, ETH Zurich. All rights reserved.
#
#  Please, refer to the LICENSE file in the root directory.
#  SPDX-License-Identifier: BSD-3-Clause
#
import subprocess, os, tempfile
from flask import Flask, request, jsonify
import functools
import jwt

AUTH_HEADER_NAME = 'Authorization'

SSH_CERT_VALIDITY = "+5m"

AUTH_AUDIENCE = os.environ.get("F7T_AUTH_TOKEN_AUD", '').strip('\'"')
AUTH_REQUIRED_SCOPE = os.environ.get("F7T_AUTH_REQUIRED_SCOPE", '').strip('\'"')

AUTH_ROLE = os.environ.get("F7T_AUTH_ROLE", '').strip('\'"')

CERTIFICATOR_PORT = os.environ.get("F7T_CERTIFICATOR_PORT", 5000)

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
        logging.error("JWT invalid signature", exc_info=True)
    except jwt.ExpiredSignatureError:
        logging.error("JWT token has expired", exc_info=True)
    except jwt.InvalidAudienceError:
        logging.error("JWT token invalid audience", exc_info=True)
    except jwt.exceptions.InvalidAlgorithmError:
        logging.error("JWT invalid signature algorithm", exc_info=True)
    except Exception:
        logging.error("Bad header or JWT, general exception raised", exc_info=True)

    return False

# receive the header, and extract the username from the token
# returns username
def get_username(header):
    if debug:
        logging.info('debug: cscs_api_common: get_username: ' + header)
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
        logging.error("JWT invalid signature", exc_info=True)
    except jwt.ExpiredSignatureError:
        logging.error("JWT token has expired", exc_info=True)
    except jwt.InvalidAudienceError:
        logging.error("JWT token invalid audience", exc_info=True)
    except jwt.exceptions.InvalidAlgorithmError:
        logging.error("JWT invalid signature algorithm", exc_info=True)
    except Exception:
        logging.error("Bad header or JWT, general exception raised", exc_info=True)

    return None

def check_auth_header(func):
    @functools.wraps(func)
    def wrapper_check_auth_header(*args, **kwargs):
        try:
            auth_header = request.headers[AUTH_HEADER_NAME]
        except KeyError:
            logging.error("No Auth Header given")
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

        app.logger.info(f"Generating cert for user: {username}")
        
        command = f"ssh-keygen -s ca-key -n {username} -V {SSH_CERT_VALIDITY} -I ca-key {td}/user-key.pub "

        app.logger.info(f"SSH keygen command: {command}")

    except Exception as e:
        logging.error(e)
        return jsonify(description=f"Error creating certificate. {e}", error=-1), 404

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
        return jsonify(description=f"Error creating certificate. {e}", error=-1), 404



if __name__ == "__main__":    
    
    app.run(debug=debug, host='0.0.0.0', port=CERTIFICATOR_PORT)
    

