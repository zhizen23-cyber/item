import bpy,math,json,bmesh
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001
# Axis Z; head underside z=0; groove near edge z=27 per diagram interpretation.
profile=[(0,-1.8),(4.25,-1.8),(4.25,0),(2.5,0),(2.5,27),(2,27),(2,27.9),(2.5,27.9),(2.5,30),(0,30)]
n=128;v=[]
for r,z in profile:
 for i in range(n):v.append((r*math.cos(2*math.pi*i/n),r*math.sin(2*math.pi*i/n),z))
f=[]
for j in range(len(profile)-1):
 for i in range(n):k=(i+1)%n;f.append((j*n+i,j*n+k,(j+1)*n+k,(j+1)*n+i))
me=bpy.data.meshes.new('Dimensioned_pin');me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new('D5_杆长30_标注有效27_槽位解释待实测',me);s.collection.objects.link(o)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
m=bpy.data.materials.new('Steel_reference');m.diffuse_color=(.48,.52,.56,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.48,.52,.56,1);p.inputs['Metallic'].default_value=.8;p.inputs['Roughness'].default_value=.26;o.data.materials.append(m)
for p in me.polygons:p.use_smooth=False
for k,val in {'shaft_diameter_mm':5.,'shaft_length_mm':30.,'effective_label_mm':27.,'head_diameter_mm':8.5,'head_thickness_mm':1.8,'groove_width_mm':.9,'groove_diameter_mm':4.}.items():o[k]=val
o['groove_position_interpretation']='近头槽边27；E卡实际接触面及槽位定义须实测。';o['source']='用户商品尺寸图，2026-11-16；未声明已拥有或载荷认证'
notes=P/'模型说明.txt'
if notes.exists():bpy.data.texts.new('尺寸来源与边界').write(notes.read_text())
# preview only camera/lights collection
c=bpy.data.collections.new('PREVIEW_ONLY');s.collection.children.link(c)
def link(obj):
 for coll in list(obj.users_collection):coll.objects.unlink(obj)
 c.objects.link(obj)
bpy.ops.object.camera_add(location=(42,-65,40));cam=bpy.context.object;link(cam);cam.rotation_euler=(Vector((0,0,14))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=42;s.camera=cam
for loc,power,size in [((20,-25,45),1800,25),((-20,-10,15),1200,20),((0,30,20),1600,20)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;link(l);l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,0,14))-l.location).to_track_quat('-Z','Y').to_euler()
s.world.color=(.4,.4,.4);s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24;s.cycles.use_denoising=False;s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(P/'预览.png')
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(P/'销轴_D5x30_有效27.blend'));bpy.ops.render.render(write_still=True)
bm=bmesh.new();bm.from_mesh(me);json.dump({'dimensions_mm':list(o.dimensions),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'volume_mm3':bm.calc_volume(),'groove_z_mm':[27,27.9]},open(P/'数字模型检查.json','w'),indent=2);bm.free()
