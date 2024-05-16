from flask import Flask, request, jsonify
import base64
import jsonpatch
import os
import logging
import json
import datetime


admission_controller = Flask(__name__)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Function to check if mutation is required
# Function to add an extra environment variable to containers
# Function to add an extra environment variable to containers
def add_extra_env(target, extra_env_var, base_path):
    patch = []
    path = base_path

    # Check if the environment variable is already present
    if not target:
        # The env block is not present, add it along with the new environment variable
        patch.append({"op": "add", "path": f"{path}", "value": [extra_env_var]})
        logger.info(f"Added the env block and the patch to the object {extra_env_var}")
    else:
        existing_var_index = next((i for i, env_var in enumerate(target) if env_var["name"] == extra_env_var["name"]), None)
        if existing_var_index is not None:
            # Environment variable is present, check if the values are different
            if target[existing_var_index].get("value") != extra_env_var["value"]:
                logger.info(f"The object already contains the env variable")
                # Modify the existing environment variable with the new value
                patch.append({"op": "replace", "path": f"{path}/{existing_var_index}/value", "value": extra_env_var["value"]})
                logger.info(f"Path applied to the existing Env and replaced the value with {extra_env_var['value']}")
        else:
            # Add the environment variable if not present
            patch.append({"op": "add", "path": f"{path}/-", "value": extra_env_var})
            logger.info(f"Added the patch to the object {extra_env_var}")

    return patch



# Main mutation process
@admission_controller.route('/mutate/deployments', methods=['POST'])
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


   if deployment['kind'] not in ['Deployment', 'Job', 'Pod']:
       logger.info(f"Not a Deployment, Job, or Pod. Kind: {deployment['kind']}")
       return admission_response_patch(res_api_ver, res_uid, False, "Not a Deployment", jsonpatch.JsonPatch([]))


   tenant_name = os.environ.get("TENANT_NAME")
   logger.info(f"Mutating {deployment['kind']} Tenant_name: {tenant_name}")

   all_patches = []
   # Define the environment variable to add
   extra_env_var = {"name": "Tenant_name", "value": tenant_name}
 
   try:
        if deployment['kind'] in ['Deployment', 'Job']:
            logger.info(f"Trying mutation on {deployment['metadata']['name']}")
            containers = deployment['spec']['template']['spec']['containers']
            for container in containers:
                logger.info(f"{container}")
                existing_env = container.get('env', [])
                logger.info(f"{existing_env}")
                
                # Generating the JSON Patch path for each container's env
                patch_path = f"/spec/template/spec/containers/{containers.index(container)}/env"
                patch = add_extra_env(existing_env, extra_env_var, patch_path)
                logger.info(f"{patch}")
                
                if patch:
                    container['env'] = apply_patch(existing_env, patch)
                    
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
                patch = add_extra_env(existing_env, extra_env_var, patch_path)
                logger.info(f"{patch}")
                
                if patch:
                    container['env'] = apply_patch(existing_env, patch)
                                      
                # Logging the mutation information
                logger.info(f"Mutated the {deployment['kind']} at time {datetime.datetime.now().strftime('%d-%m-%Y- %H:%M:%S')}")
                logger.info("--------------END-----------------")
                all_patches.extend(patch)
                logger.info(f"the patch is {all_patches}")


   except KeyError as e:
       logger.info(f"Failed to modify {deployment['kind']}. Key error: {e}")
       return admission_response_patch(res_api_ver, res_uid, False, f"Failed to modify {deployment['kind']}", jsonpatch.JsonPatch([]))

   return admission_response_patch(res_api_ver, res_uid, True, "Added MY_ENV_VARIABLE", all_patches)

def apply_patch(existing_env, patch):
    patched_env = existing_env.copy()
    json_patch = jsonpatch.JsonPatch(patch)
    logger.info(json_patch)
            
    return json_patch





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


if __name__ == '__main__':
   admission_controller.run(host='0.0.0.0', port=5000)


# from flask import Flask, request, jsonify
# import base64
# import jsonpatch
# import os
# import logging

# admission_controller = Flask(__name__)

# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# @admission_controller.route('/mutate/deployments', methods=['POST'])
# def deployment_webhook_mutate():
#     body = request.json
#     res_api_ver = body["apiVersion"]
#     res_uid = body["request"]["uid"]

#     request_info = request.get_json()

#     try:
#         deployment = request_info['request']['object']
#         logger.info(f"Processing {deployment['kind']}")
#     except KeyError as e:
#         logger.info(f"Request JSON: {request_info}")
#         return admission_response_patch(res_api_ver, res_uid, False, "Failed to extract object_name", jsonpatch.JsonPatch([]))

#     # Check if the object is a Deployment, Job, or Pod
#     if deployment['kind'] not in ['Deployment', 'Job', 'Pod']:
#         logger.info(f"Not a Deployment, Job, or Pod. Kind: {deployment['kind']}")
#         return admission_response_patch(res_api_ver, res_uid, False, "Not a Deployment", jsonpatch.JsonPatch([]))

#     # Get the value of tenant from the environment variable
#     tenant_name = os.environ.get("TENANT_NAME")
#     logger.info(f"Mutating {deployment['kind']} Tenant_name: {tenant_name}")

#     # Define the environment variable to add
#     new_env_var = {"name": "Tenant_name", "value": tenant_name}

#     try:
#         if deployment['kind'] in ['Deployment', 'Job']:
#             containers = deployment['spec']['template']['spec']['containers']
#             for container in containers:
#                 existing_env = container.get('env', [])
#                 existing_env_names = {env_var['name'] for env_var in existing_env}
                
#                 # Check if the new env variable is already present
#                 if 'Tenant_name' not in existing_env_names:
#                     container['env'] = existing_env + [new_env_var]
                    
#         elif deployment['kind'] == 'Pod':
#             containers = deployment['spec']['containers']
#             for container in containers:
#                 existing_env = container.get('env', [])
#                 existing_env_names = {env_var['name'] for env_var in existing_env}
#         # Check if the new env variable is already present
#                 if 'Tenant_name' not in existing_env_names:
#                     container['env'] = existing_env + [new_env_var]
#     except KeyError as e:
#         logger.info(f"Failed to modify {deployment['kind']}. Key error: {e}")
#         return admission_response_patch(res_api_ver, res_uid, False, f"Failed to modify {deployment['kind']}", jsonpatch.JsonPatch([]))

#     # Create a JSON patch to update the Deployment or Pod
#     json_patch_path = "/spec/template/spec/containers/0/env/-"
#     if deployment['kind'] == 'Pod':
#         # Adjust the JSON path for Pods
#         json_patch_path = "/spec/containers/0/env/-"


#     json_patch = jsonpatch.JsonPatch([
#         {"op": "add", "path": json_patch_path, "value": [new_env_var]}
#     ])
#     logger.info(f"Added Env Variable to {deployment['kind']}")
    
#     admission_review_log = {
#     "apiVersion": res_api_ver,
#     "kind": "AdmissionReview",
#     "request": request_info['request'],
#     "response": {
#         "uid": res_uid,
#         "allowed": True,
#         "status": {"message": "Added MY_ENV_VARIABLE"},
#         "patchType": "JSONPatch",
#         "patch": json_patch.to_string()
#         }
#     }
#     logger.debug(f"Admission Review Log: {admission_review_log}")

#     return admission_response_patch(res_api_ver, res_uid, True, "Added MY_ENV_VARIABLE", json_patch)

# def admission_response_patch(api_version, uid, allowed, message, json_patch):
#     base64_patch = base64.b64encode(json_patch.to_string().encode("utf-8")).decode("utf-8")
#     return jsonify({
#         "apiVersion": api_version,
#         "kind": "AdmissionReview",
#         "response": {
#             "uid": uid,
#             "allowed": allowed,
#             "status": {"message": message},
#             "patchType": "JSONPatch",
#             "patch": base64_patch
#         }
#     })

# if __name__ == '__main__':
#     admission_controller.run(host='0.0.0.0', port=5000)
