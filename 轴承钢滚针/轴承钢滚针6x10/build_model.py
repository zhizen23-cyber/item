# Run: blender -b --python build_model.py
import bpy, math, os, bmesh, json
from mathutils import Vector
D,L=6,10
R=min(D*0.05,0.25) # Unmarked edge radius, display assumption only.
OUT=os.path.dirname(os.path.abspath(__file__))
NAME='轴承钢滚针%gx%g'%(D,L)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001;sc.unit_settings.length_unit='MILLIMETERS'
N=192;profile=[]
for j in range(9):
 a=-math.pi/2+j*math.pi/16;profile.append((D/2-R+R*math.cos(a),R+R*math.sin(a)))
for j in range(9):
 a=j*math.pi/16;profile.append((D/2-R+R*math.cos(a),L-R+R*math.sin(a)))
v=[(r*math.cos(i*2*math.pi/N),r*math.sin(i*2*math.pi/N),z) for r,z in profile for i in range(N)]
f=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(len(profile)-1) for i in range(N)]
f.extend([tuple(reversed(range(N))),tuple((len(profile)-1)*N+i for i in range(N))])
me=bpy.data.meshes.new(NAME+'_封闭实体');me.from_pydata(v,[],f);me.update()
o=bpy.data.objects.new(NAME,me);bpy.context.collection.objects.link(o)
for p in me.polygons:p.use_smooth=len(p.vertices)==4
mat=bpy.data.materials.new('轴承钢_展示材质');mat.use_nodes=True
p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.5,.55,.61,1);p.inputs['Metallic'].default_value=.95;p.inputs['Roughness'].default_value=.24;o.data.materials.append(mat)
o['标称直径_mm']=D;o['标称总长_mm']=L;o['端部圆角半径_假定_mm']=R
o['依据']='同目录原始照片包装规格；不含公差、硬度、牌号或精度等级确认'
notes=f'''{NAME} | 照片参考模型\n依据：同目录原始 JPG，已目视核对包装“高精度轴承钢滚针”，规格 {D:g}×{L:g}。\n尺寸含义：直径 {D:g} mm、总长度 {L:g} mm。采用毫米建模，轴线为 Z，底端 z=0，顶端 z={L:g}。\n可见实物为光滑实心圆柱、平端面，边缘有轻微修整。照片未给出圆角/倒角尺寸；本模型两端取 R{R:g} mm 圆角，仅为外观近似。\n材质名称按包装“轴承钢”记录；不擅自认定 GCr15、硬度、直径公差、圆度、精度等级或执行标准。\n用于布置与原理展示；精密配合需实测或供应商尺寸图。圆角不是采购保证值。\n修改 build_model.py 顶部 D、L、R 可重新生成；主体为独立封闭网格。相机、灯光和背景仅用于预览。\n'''
bpy.data.texts.new('尺寸依据与假定').write(notes);open(os.path.join(OUT,'模型说明.txt'),'w').write(notes)
bm=bmesh.new();bm.from_mesh(me);assert sum(not e.is_manifold for e in bm.edges)==0;bm.free()
bpy.context.view_layer.update();assert all(abs(a-b)<1e-5 for a,b in zip(o.dimensions,(D,D,L)))
print('VALIDATED',NAME,tuple(o.dimensions),'nonmanifold=0')
# Isolate studio from reusable component.
c=bpy.data.collections.new('预览_相机灯光地面');sc.collection.children.link(c)
def studio(obj):
 for old in list(obj.users_collection):old.objects.unlink(obj)
 c.objects.link(obj)
def aim(obj,p):obj.rotation_euler=(Vector(p)-obj.location).to_track_quat('-Z','Y').to_euler()
S=max(L,D*1.8)
bpy.ops.mesh.primitive_plane_add(size=S*15,location=(0,0,-.01));fl=bpy.context.object;fl.name='预览地面';studio(fl)
fm=bpy.data.materials.new('Studio dark');fm.diffuse_color=(.05,.065,.08,1);fl.data.materials.append(fm)
for pos,energy,size in [((S,-S,S*1.7),S*S*15,S),((-S,S*.3,S),S*S*20,S*.7),((0,S,S*.5),S*S*10,S*.7)]:
 bpy.ops.object.light_add(type='AREA',location=pos);li=bpy.context.object;li.data.energy=energy;li.data.size=size;aim(li,(0,0,L/2));studio(li)
bpy.ops.object.camera_add(location=(S*1.5,-S*2,S*1.4+L/2));cam=bpy.context.object;aim(cam,(0,0,L/2));cam.data.type='ORTHO';cam.data.ortho_scale=max(L*1.25,D*2.2);sc.camera=cam;studio(cam)
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=False;sc.world.color=(.2,.2,.2)
sc.render.resolution_x=700;sc.render.resolution_y=700;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX'
sc.render.image_settings.file_format='PNG';sc.render.filepath=os.path.join(OUT,NAME+'_预览.png')
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_location=(0,0,L/2);a.spaces.active.region_3d.view_distance=S*2
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,NAME+'.blend'),compress=True)
bpy.ops.render.render(write_still=True)
