## Paste to UE

Blender plugin to copy objects from Blender to UE as blueprints

### Installation

Download zip file from the [releases](https://github.com/joric/paste_to_ue/releases) section, install it as blender plugin.

### Usage

Select objects, press Ctrl+Shift+C to copy objects data. You also can click "Object > Paste to UE" in menu.

Clipboard Format:

```python
eli,eal=unreal.EditorLevelLibrary,unreal.EditorAssetLibrary
load=lambda bp:eal.load_blueprint_class(eal.load_asset(bp).get_outer().get_full_name())
add=lambda bp,v,r:eli.spawn_actor_from_class(load(bp),unreal.Vector(*v),unreal.Rotator(*r))
add("/Game/Items/BP_Item",(1,1,1),(2,2,2))
add("/Game/Items/BP_Coin",(1,1,1),(2,2,2)).set_actor_scale3d(unreal.Vector{3,3,3}) # optional
# ...
```

Paste it to UE5 "Python" window (not REPL), it allows multiline text.

You can specify blueprint and scale in the popup menu.
Scale needs to be different from 0 to apply scene scale, use with caution.
You can scale objects preserving origins in UE by selecting objects and changing scale in properties.

### Mesh Separation

There's also some work on point cloud matching for joined objects and mesh align but it's WIP.

### References

* https://github.com/NazzarenoGiannelli/coordiknight similar plugin, pastes cubes
* https://www.sidefx.com/forum/topic/58153/ 3 point align of 2 similar meshes (like in Maya)
* https://github.com/egtwobits/mesh_mesh_align_plus
* https://blenderartists.org/t/how-to-calculate-rotation-for-mesh2-based-on-identical-mesh1-and-its-local-vertices-data/1329857/5
