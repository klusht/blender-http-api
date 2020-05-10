# Blender 3D http api
### workaround 

## Description
- Simple script file that will allow controlling blender program via an http endpoint
- This will start a separate thread from python that will be listening on localhost:8000

There are two modes for the moment:
- sync: will execute the commands in a separate thread (not safe)
- async: will schedule the command to be evaluated in the MainThread every second (safe)


#### Warning
- Blender team does not recommend accessing the bpy context from a thread different from MainThread.
- There are numerous cases where blender will crash with Segmentation fault, hence constantly saving your progress as even scheduling to be executed in the MainThread can cause problems.


## Installation
#### Under Scripting window, create a new text file pass the content of blender_simple_http_api.py 
#### click *Run Script* ONCE
- The running thread that keeps port 8000 in use cannot be killed from the script, hence to make changes or stop the server you need to quit blender


## Usage
- To make the apy as flexible as possible there is no JSON serialization in the response, but it can be achieved using json.dumps
- 

### SYNC 
- POST Retrieve raw python data
`curl --data "dir(bpy.data.objects['Cube'])" localhost:8000/sync`
 
- POST Retrieve as json 
`curl --data "json.dumps(dir(bpy.data.objects['Cube']))" localhost:8000/sync`
 
- POST Retrieve X location of an object
`curl --data "bpy.data.objects['Cube'].location.x" localhost:8000/sync`
 
- GET Object property value ( will execute the same command as the one above )
`curl localhost:8000/Cube/location/x`   Expected: 0.0
 
- GET Object properties 
`curl localhost:8000/Cube/location`     Expected: <Vector (3.1146, 8.0631, 4.8566)>
 
- POST Move object
`curl --data "bpy.data.objects['Cube'].location.x += 0.05" localhost:8000/sync`
 
- POST Accessing actions that depends on context view: FAILS ( works in python interpreter )
`curl --data "bpy.ops.object.editmode_toggle()" localhost:8000/sync`  >>> throws error as context is not VIEW 3D
 
 
 
## ASYNC 
All commands are executed in main Thread that should avoid Segmentation faults but no data can be retrieved as there is no pub-sub queue implementation
 
- This is still crashing blender as it is missing the context ( know bug ?? )
`curl --data "bpy.ops.mesh.primitive_cube_add(location=(4,-3,6))" localhost:8000/async`
 
- Add object cube workaround
`curl --data "bpy.ops.mesh.primitive_cube_add({'window': bpy.context.window_manager.windows[0], 'screen': bpy.context.window_manager.windows[0].screen}, location=(4,-3, 6))" localhost:8000/async`
 
 
## DIRECT METHOD CALL
You can store functions in driver_namespace object and then call the function directly passing the content of the POST as a single string argument. You can change/update the function in every "Run Script"
 
Example:
Create a complex function and save the reference in bpy.app.driver_namespace

```
import bpy
import threading
 
def cube(args_str):
    print(threading.current_thread().name, "Executing cube function")
    window = bpy.context.window_manager.windows[0]
    ctx = {'window': window, 'screen': window.screen}
    location_parts = args_str.split(',')
    bpy.ops.mesh.primitive_cube_add(ctx, location=(float(location_parts[0]),float(location_parts[1]),float(location_parts[2])))
 
bpy.app.driver_namespace["cube"] = cube
```
- Using POST pass the values as a single string that you need to split inside the function

```
curl --data "4,-3,6" localhost:8000/cube

```
