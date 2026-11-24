"""Standalone nominal-dimension Blender model of the photographed split shaft support.
Run: blender -b -P build_model.py -- /absolute/output/directory
"""
import bpy,bmesh,math
from mathutils import Vector
from pathlib import Path
def mesh(name,verts,faces,col):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    ob=bpy.data.objects.new(name,me);col.objects.link(ob);return ob
def prism(name,points,x0,x1,col):
    n=len(points);return mesh(name,[(x,y,z) for x in (x0,x1) for y,z in points],[tuple(range(n)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],col)
def box(name,low,high,col):
    a,b,c=low;d,e,f=high;return prism(name,[(b,c),(e,c),(e,f),(b,f)],a,d,col)
def revolved(name,axis,cy,cz,profiles,col,n=48,phase=0):
    def pos(q,r,i):
        u=cy+r*math.cos(math.tau*i/n+phase);v=cz+r*math.sin(math.tau*i/n+phase)
        return (q,u,v) if axis=='X' else (u,q,v) if axis=='Y' else (u,v,q)
    p=len(profiles);return mesh(name,[pos(q,r,i) for q,r in profiles for i in range(n)],
        [tuple(range(n)),tuple(range((p-1)*n,p*n))]+[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(p-1) for i in range(n)],col)
def diff(ob,cut):
    bpy.context.view_layer.update()
    md=ob.modifiers.new('machined opening','BOOLEAN');md.operation='DIFFERENCE';md.solver='MANIFOLD';md.object=cut
    with bpy.context.temp_override(object=ob,active_object=ob,selected_objects=[ob]):bpy.ops.object.modifier_apply(modifier=md.name)
    d=cut.data;bpy.data.objects.remove(cut,do_unlink=True);bpy.data.meshes.remove(d)
def material(name,rgb,met=.65):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Metallic'].default_value=met;p.inputs['Roughness'].default_value=.37
    return m
def make_shf(col,prefix='ITEM_SHF20'):
    # Dimensions on supplied drawing stay exact. Corner and edge relief and screw details are illustrative.
    pts=[(-29.4,-30.8),(29.4,-30.8),(29.4,-20.8),(15,-20.8),(15,20),(-15,20),(-15,-20.8),(-29.4,-20.8)]
    ob=prism(prefix+'_BODY',pts,-9.8,9.8,col)
    diff(ob,revolved('cut', 'X',0,0,[(-11,10.45),(-9.8,10.45),(-9.35,10),(9.35,10),(9.8,10.45),(11,10.45)],col,128))
    diff(ob,box('cut',(-10.2,-.65,9.7),(10.2,.65,21),col))
    for y in [-22.35,22.35]:
        diff(ob,revolved('cut','Z',0,y,[(-31.2,3.48),(-30.8,3.48),(-30.62,3.3),(-20.98,3.3),(-20.8,3.48),(-20.4,3.48)],col,64))
    diff(ob,revolved('cut','Y',0,15.0,[(-16,4.5),(-8.5,4.5),(-8.49,2.70),(.18,2.70)],col,64))
    diff(ob,revolved('cut','Y',0,15.0,[(.12,2.10),(15.5,2.10)],col,64))
    bolt=revolved(prefix+'_M5x25_SOCKET_SCREW','Y',0,15.0,[(-13.5,4.05),(-13.21,4.25),(-8.7,4.25),(-8.5,4.09),(-8.498,2.49),(16.1,2.49),(16.5,2.1)],col,64)
    diff(bolt,revolved('cut','Y',0,15,[(-14,2.31),(-10,2.31)],col,6,math.pi/6))
    ob.data.materials.append(material('SHF20 • machined aluminium',(.57,.64,.70)))
    bolt.data.materials.append(material('SHF20 • black oxide steel',(.075,.085,.10),.85))
    for x in [ob,bolt]:
        x['source']='尺寸来自用户提供的单批次测量示意；未标注细节为近似。商品型号尚未核对。'
    ob['envelope_W_X_Z_mm']='58.8 / 19.6 / 50.8'
    ob['shaft_D_mm']=20.;ob['mount_cc_mm']=44.7;ob['mount_hole_mm']=6.6
    return ob,bolt
def quality(o):
    b=bmesh.new();b.from_mesh(o.data);v=b.calc_volume(signed=True);bad=sum(not e.is_manifold for e in b.edges);b.free()
    assert v>0 and bad==0,(o.name,v,bad);return tuple(round(x,4) for x in o.dimensions),v
def asset(dirname):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene;s.name='Ø20 split shaft support | Item'
    s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001;s.unit_settings.length_unit='MILLIMETERS'
    col=bpy.data.collections.new('Ø20立式开口光轴固定座');s.collection.children.link(col)
    for o in make_shf(col):print('GEOMETRY',o.name,quality(o));o.asset_mark()
    data=bpy.data.cameras.new('Item preview');cam=bpy.data.objects.new(data.name,data);s.collection.objects.link(cam);s.camera=cam
    target=Vector((0,0,-5));cam.location=(114,-92,70);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO';data.ortho_scale=91
    s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=900;s.render.resolution_y=740;s.render.resolution_percentage=100
    d=s.display.shading;d.light='STUDIO';d.color_type='MATERIAL';d.show_cavity=True;d.cavity_type='BOTH';d.show_shadows=True;d.show_specular_highlight=True;d.background_type='WORLD';s.world=bpy.data.worlds.new('Background');s.world.color=(.18,.18,.18)
    for screen in bpy.data.screens:
        for a in screen.areas:
            if a.type=='VIEW_3D':
                rv=a.spaces.active.region_3d;rv.view_distance=125;rv.view_location=target;rv.view_rotation=cam.rotation_euler.to_quaternion();a.spaces.active.clip_end=10000
    dirname.mkdir(exist_ok=True,parents=True);s.render.filepath=str(dirname/'preview.png')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(dirname/'D20_split_shaft_support.blend'),compress=True)
    bpy.ops.render.render(write_still=True)
if __name__=='__main__':
    import sys
    asset(Path(sys.argv[-1]).resolve())
