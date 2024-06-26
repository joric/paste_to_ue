## Paste to UE

Blender plugin to copy objects position (and transformations) from Blender to Unreal Engine as blueprints

### Installation

Download the latest release from the [releases](../../releases) section, install it as blender plugin.

### Usage

All actions are available from the tool panel (press N, select "Paste to UE" tab).

#### Auto Mesh Separation

Experimental function, splits mesh into templates and instances with a single button.
Depends on a Blender's built-in function "split by loose parts" that changes topology
so it may be unreliable (e.g. rotation may be off). "Match Templates" is usually more accurate.

#### Match Templates

Prepare templates, select all related objects (the largest will be cloud,
the rest will be the templates), press "Create Instances" from the tool panel (or press Ctrl+Shift+D).
It will find and create template instances with matching scaling/rotation.

Object matching algorithm currently uses weighted distance between the points.
Adjust delta to large value if objects don't match the templates (e.g. set to 1).
If it doesn't fix it, try separating the large mesh into smaller meshes
by template type and match single templates.

##### Video

[![](http://img.youtube.com/vi/lSLK26Li14w/hqdefault.jpg)](https://youtu.be/lSLK26Li14w)

#### Copy Transforms

Select objects, press Ctrl+Shift+C to copy objects data. You also can click "Copy to Clipboard" in the tool panel.
Clipboard Format:

```python
eli,eal=unreal.EditorLevelLibrary,unreal.EditorAssetLibrary
load=lambda bp:eal.load_blueprint_class(eal.load_asset(bp).get_outer().get_full_name())
add=lambda bp,v,r:eli.spawn_actor_from_class(load(bp),unreal.Vector(*v),unreal.Rotator(*r))
add("/Game/Items/BP_Item",(1,1,1),(2,2,2))
add("/Game/Items/BP_Coin",(1,1,1),(2,2,2)).set_actor_scale3d(unreal.Vector{3,3,3}) # optional
# ...
```

Paste clipboard to the UE5 "Python" window (not REPL), it allows multiline text.
You can also specify blueprint and scale in the toolbar (use with caution, scale is taken from the scene).
You can also apply scale for all selected objects in UE without moving them by changing scale value in properties.

### References

* https://github.com/joric/io_scene_b3d Blitz3d import plugin
* https://github.com/NazzarenoGiannelli/coordiknight pastes transformations as cubes
* https://www.sidefx.com/forum/topic/58153/ 3 point align of 2 similar meshes (like in Maya)
* https://github.com/egtwobits/mesh_mesh_align_plus Mesh Align Plus
* https://blenderartists.org/t/how-to-calculate-rotation-for-mesh2-based-on-identical-mesh1-and-its-local-vertices-data/1329857/5
* https://nghiaho.com/?page_id=671 Finding optimal rotation and translation between corresponding 3d points
* https://gist.github.com/nh2/bc4e2981b0e213fefd4aaa33edfb3893 rigid-transform-with-scale.py

