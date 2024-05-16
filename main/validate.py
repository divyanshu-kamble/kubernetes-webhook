from flask import Flask, request, jsonify
import base64
import jsonpatch
import os
import logging
import json
import datetime


# Initialize Flask app
admission_controller = Flask(__name__)


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Function to add an extra environment variable to containers and check if the env variable exists and its value
def add_extra_env(existing_env, new_env_var, base_path):
   patch = []
   path = base_path
   # Check if the environment variable is already present
   if not existing_env:
       # The env block is not present, add it along with the new environment variable
       patch.append({"op": "add", "path": f"{path}", "value": [new_env_var]})
       logger.info(f"Added the env block and the patch to the object {new_env_var}")
   else:
       #Check the index of new_env_var in the existing_env list
       existing_var_index = next((i for i, env_var in enumerate(existing_env) if env_var["name"] == new_env_var["name"]), None)


       if existing_var_index is not None:
           # Environment variable is present, check if the values are different
           if existing_env[existing_var_index].get("value") != new_env_var["value"]:
               logger.info(f"The object already contains the env variable with different value")


               # Modify the existing environment variable with the new value
               patch.append({"op": "replace", "path": f"{path}/{existing_var_index}/value", "value": new_env_var["value"]})
               logger.info(f"Path applied to the existing Env and replaced the value with {new_env_var['value']}")
       else:
           # Add the environment variable if not present
           patch.append({"op": "add", "path": f"{path}/-", "value": new_env_var})
           logger.info(f"Added the patch to the object {new_env_var}")
   return patch

# Function to generate admission response with patch
def admission_response_patch(api_version, uid, allowed, message, json_patch):
  base64_patch = base64.b64encode(json.dumps(json_patch).encode("utf-8")).decode("utf-8")
  return jsonify({
      "apiVersion": api_version,
      "kind": "AdmissionReview",
      "response": {
          "uid": uid,
          "allowed": allowed,
          "status": {"message": message},
          "patchType": "JSONPatch",
          "patch": base64_patch
      }
  })


# Main mutation Function
@admission_controller.route('/mutate/webhook', methods=['POST'])
def deployment_webhook_mutate():
  body = request.json
  res_api_ver = body["apiVersion"]
  res_uid = body["request"]["uid"]
  request_info = request.get_json()
  try:
      deployment = request_info['request']['object']
      logger.info("--------------RESPONSE-----------------")
      logger.info(f"Processing {deployment['kind']}")

  except KeyError as e:
      logger.info(f"Request JSON: {request_info}")
      return admission_response_patch(res_api_ver, res_uid, False, "Failed to extract object_name", jsonpatch.JsonPatch([]))
  if deployment['kind'] not in ['Deployment', 'Pod']:
      logger.info(f"Not a Deployment or Pod. Kind: {deployment['kind']}")
      return admission_response_patch(res_api_ver, res_uid, False, "Not a Deployment", jsonpatch.JsonPatch([]))


  webhook_test = os.environ.get("WEBHOOK_TEST")
  logger.info(f"Mutating {deployment['kind']} Webhook_test: {webhook_test}")
  all_patches = []
  # Define the environment variable to add
  new_env_var = {"name": "Webhook_test", "value": webhook_test}
  try:
       if deployment['kind'] in ['Deployment']:
           logger.info(f"Trying mutation on {deployment['metadata']['name']}")
           containers = deployment['spec']['template']['spec']['containers']
           for container in containers:
               logger.info(f"{container}")
               existing_env = container.get('env', [])
               logger.info(f"{existing_env}")
             
               # Generating the JSON Patch path for each container's env
               patch_path = f"/spec/template/spec/containers/{containers.index(container)}/env"
               patch = add_extra_env(existing_env, new_env_var, patch_path)
               logger.info(f"{patch}")
             
               if patch:
                   container['env'] = jsonpatch.JsonPatch(patch)
                 
               # Logging the mutation information
               logger.info(f"Mutated the {deployment['kind']}:{deployment['metadata']['name']} at time {datetime.datetime.now().strftime('%d-%m-%Y- %H:%M:%S')}")
               logger.info("--------------END-----------------")
               logger.info("\n")
               all_patches.extend(patch)
               logger.info(f"the patch is {all_patches}")
             
       elif deployment['kind'] == 'Pod':
           containers = deployment['spec']['containers']
           for container in containers:
               logger.info(f"{container}")
               existing_env = container.get('env', [])
               logger.info(f"{existing_env}")
               # Generating the JSON Patch path for each container's env
               patch_path = f"/spec/containers/{containers.index(container)}/env"
               patch = add_extra_env(existing_env, new_env_var, patch_path)
               logger.info(f"{patch}")
             
               if patch:
                   container['env'] = jsonpatch.JsonPatch(patch)
                                   
               # Logging the mutation information
               logger.info(f"Mutated the {deployment['kind']} at time {datetime.datetime.now().strftime('%d-%m-%Y- %H:%M:%S')}")
               logger.info("--------------END-----------------")
               all_patches.extend(patch)
               logger.info(f"the patch is {all_patches}")

  except KeyError as e:
      logger.info(f"Failed to modify {deployment['kind']}. Key error: {e}")
      return admission_response_patch(res_api_ver, res_uid, False, f"Failed to modify {deployment['kind']}", jsonpatch.JsonPatch([]))

  return admission_response_patch(res_api_ver, res_uid, True, "Added MY_ENV_VARIABLE", all_patches)


if __name__ == '__main__':
   admission_controller.run(host='0.0.0.0', port=5000)
