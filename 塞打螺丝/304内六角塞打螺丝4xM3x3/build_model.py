import bpy, math, os, json, bmesh
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for col in list(bpy.data.collections):
 if col.name!='Collection': bpy.data.collections.remove(col)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=0.001;scene.unit_settings.length_unit='MILLIMETERS'
# mm; label supports D4 / M3 / shoulder L3. Other dimensions are explicit provisional values.
P=dict(shoulder_diameter=4.0,shoulder_length=3.0,thread_major=3.0,thread_pitch=0.5,thread_length_ASSUMED=5.0,head_diameter_ASSUMED=7.0,head_height_ASSUMED=3.0,socket_AF_ASSUMED=2.0,socket_depth_ASSUMED=1.8)
N=192; rings=[]
# Thread surface follows a continuous 0.5 mm helix with flattened crest/root and tapered runout.
for j in range(401):
 z=-8+j*5/400
 radii=[]
 for i in range(N):
  a=2*math.pi*i/N; phase=((z+8)/.5-a/(2*math.pi))%1
  d=abs(phase-.5)
  t=max(0,min(1,(.4375-d)/.3125))
  depth=.3067
  r=1.1933+depth*t
  taper=min(1,max(0,(z+8)/.3),max(0,(-3-z)/.25))
  r=1.1933+(r-1.1933)*taper
  if z < -7.8: r-=.2*(1-(z+8)/.2)
  radii.append(r)
 rings.append((z,radii))
for z,r in [(-3,1.85),(-2.85,2),(-.12,2),(0,2.12),(0,3.3),(.2,3.5),(2.8,3.5),(3,3.3)]: rings.append((z,[r]*N))
verts=[(r[i]*math.cos(2*math.pi*i/N),r[i]*math.sin(2*math.pi*i/N),z) for z,r in rings for i in range(N)]
faces=[]
for j in range(len(rings)-1):
 for i in range(N): faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
faces += [tuple(reversed(range(N))),tuple((len(rings)-1)*N+i for i in range(N))]
mesh=bpy.data.meshes.new('Shoulder_screw_continuous_helix_mm');mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new('304_内六角塞打螺丝_D4_M3_L3_待核头牙尺寸',mesh);bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
# Actual recessed hex socket, not a painted mark.
bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=2/math.sqrt(3),depth=2.2,location=(0,0,2.3))
cut=bpy.context.object;cut.name='Socket_cutter'
bpy.context.view_layer.objects.active=obj
mod=obj.modifiers.new('内六角凹槽_AF2_假定','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
for p in obj.data.polygons:p.use_smooth=len(p.vertices)==4
mat=bpy.data.materials.new('304 Stainless Steel');mat.diffuse_color=(.48,.52,.57,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.48,.52,.57,1);bs.inputs['Metallic'].default_value=.93;bs.inputs['Roughness'].default_value=.23;obj.data.materials.append(mat)
for k,v in P.items():obj[k]=v
obj['dimension_status']='Label: 4*M3*3; interpreted as shoulder diameter 4 / thread M3 / shoulder length 3. Head, socket, thread length provisional. Not manufacturing drawing.'
notes='''304 内六角塞打螺丝 4×M3×3｜照片参考模型\n原图包装仅有 4*M3*3，未附尺寸图。\n按常见规格含义解释：肩径 4 mm、M3 螺纹、肩长 3 mm。M3 使用常用粗牙螺距 0.5 mm。\n以下是建模假定，照片无法精确确认：头径 7 mm、头高 3 mm、螺纹长度 5 mm、内六角对边 2 mm、槽深 1.8 mm。\n模型采用毫米单位；肩部下表面 z=-3、头下表面 z=0，头顶 z=3，螺纹末端 z=-8。\n有真实螺旋牙和内六角凹槽；牙底、倒角与退刀槽仅为装配/展示近似，不含公差认证。\n不要据此直接加工或验证极限装配；请先实测头径、头高、牙长及扳手尺寸。\n运行同目录 build_model.py 可修改生成脚本中的几何尺寸并重新生成。没有修改原始图片。\n'''
bpy.data.texts.new('尺寸依据_先读').write(notes)
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes)
# Presentation collection isolated from reusable screw.
col=bpy.data.collections.new('Preview_only_灯光地面相机');scene.collection.children.link(col)
def to_preview(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-8.03));floor=bpy.context.object;floor.name='Preview_floor';to_preview(floor)
fm=bpy.data.materials.new('Studio charcoal');fm.diffuse_color=(.055,.07,.09,1);floor.data.materials.append(fm)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Key', (8,-10,13),1800,9),('Rim',(-8,5,7),2200,7),('Fill',(5,7,-1),1400,8)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,-2));to_preview(o)
bpy.ops.object.camera_add(location=(17,-22,16));cam=bpy.context.object;aim(cam,(0,0,-2));cam.data.type='ORTHO';cam.data.ortho_scale=17.5;scene.camera=cam;to_preview(cam)
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=False
scene.world.color=(.2,.2,.2);scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(OUT,'304_4xM3x3_预览.png')
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_distance=23;a.spaces.active.region_3d.view_location=(0,0,-2)
bm=bmesh.new();bm.from_mesh(obj.data)
report={'dimensions_mm':list(obj.dimensions),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'vertices':len(obj.data.vertices),'parameters':P};bm.free()
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'304_内六角塞打螺丝_4xM3x3.blend'),compress=True)
bpy.ops.render.render(write_still=True)
print('CHECK',report)
