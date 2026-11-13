P={'M': 5, 'L_assumed': 10, 'D_assumed': 7, 'label': '5*10*7', 'dimension_order_confirmed': False}
import bpy,bmesh,math,json,os
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001;sc.unit_settings.length_unit='MILLIMETERS'
M,L,D=P['M'],P['L_assumed'],P['D_assumed'];pitch={2:.4,3:.5,4:.7,5:.8}[M]
N=160;NZ=100;vs=[];fs=[]
# One watertight annular mesh. Opposite diagonal knurl bands are illustrative.
for j in range(NZ+1):
 z=L*j/NZ
 edge=min(1,z/.15,(L-z)/.15)
 band=1 if .08*L<z<.43*L or .57*L<z<.92*L else 0
 for i in range(N):
  a=2*math.pi*i/N;phase=a*20+(z/L)*24*(1 if z<L/2 else -1)
  r=D/2-.08*(1-edge)-band*.16*(.5+.5*math.cos(phase))
  if .43*L<=z<=.57*L:r-=.18
  vs.append((r*math.cos(a),r*math.sin(a),z))
for j in range(NZ+1):
 z=L*j/NZ
 for i in range(N):
  a=2*math.pi*i/N;ph=(z/pitch-a/(2*math.pi))%1
  # nominal internal thread crests/troughs, simplified without fit tolerance
  r=M/2-.54*pitch*(1-abs(ph-.5)*2)
  if z<.12 or z>L-.12:r=M/2+.06
  vs.append((r*math.cos(a),r*math.sin(a),z))
base=(NZ+1)*N
for b in [0,base]:
 for j in range(NZ):
  for i in range(N):
   q=(b+j*N+i,b+j*N+(i+1)%N,b+(j+1)*N+(i+1)%N,b+(j+1)*N+i);fs.append(q if b==0 else tuple(reversed(q)))
for i in range(N):
 k=(i+1)%N;fs.append((i,base+i,base+k,k));fs.append((NZ*N+i,NZ*N+k,base+NZ*N+k,base+NZ*N+i))
me=bpy.data.meshes.new(NAME);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(NAME,me);bpy.context.collection.objects.link(o)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.to_mesh(me);bm.free();assert bad==0 and vol>0
for p in me.polygons:p.use_smooth=True
m=bpy.data.materials.new('黄铜外观_牌号未确认');m.diffuse_color=(.58,.35,.09,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Metallic'].default_value=.78;bs.inputs['Roughness'].default_value=.3;o.data.materials.append(m)
for k,v in P.items():o[k]=v
notes=f'''{NAME}：照片标签参考模型，不是精确实测件。
照片原标签：{P['label']}。暂按“螺纹M × 长度 × 外径”解释为 M{M}、长{L}、外径{D} mm；其中长度/外径顺序仍待核对，不将推断当实测事实。
M4×10×6、M5×10×7与已有订单规格可对应；照片中的细长外观支持此顺序，但非尺寸测量证据。其他标签沿用同一解释，不能因此视作确认。
照片显示黄色金属嵌件，按黄铜外观表达；材料牌号未知。双段对向斜滚花、腰槽、导入倒角、内部螺距和牙型均为建模参考，不声称还原实物滚花形状。标签“土八”保留在依据中，未认定为标准号或厂商。
原点底面中心，+Z为孔轴；1单位=1mm。内部M{M}螺距暂按常用粗牙{pitch}mm，未有实测或厂家图确认。
仅可用于库存识别/初步布置，不可直接确定热熔预孔、压装过盈、抗拔力或加工参数。尤其不要根据本模型反推打印预孔尺寸。无标签的中下格未建模。
'''
bpy.data.texts.new('先读_尺寸假设与边界').write(notes)
open(os.path.join(OUT,'README.md'),'w').write('# '+NAME+'\n\n![预览]('+NAME+'_预览.png)\n\n'+notes+'\n[Blender模型]('+NAME+'.blend)')
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes)
bpy.context.view_layer.update();dims=list(o.dimensions);assert abs(dims[2]-L)<1e-5
report={'parameters':P,'dimensions_mm':dims,'nonmanifold_edges':bad,'volume_mm3':vol,'scope':'标签顺序假设，待核；非制造模型'}
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(report,ensure_ascii=False,indent=2))
col=bpy.data.collections.new('预览专用');sc.collection.children.link(col)
def move(a):
 for c in list(a.users_collection):c.objects.unlink(a)
 col.objects.link(a)
def aim(a,t):a.rotation_euler=(Vector(t)-a.location).to_track_quat('-Z','Y').to_euler()
span=max(D,L);target=(0,0,L*.45)
bpy.ops.mesh.primitive_plane_add(size=span*20,location=(0,0,-.03));a=bpy.context.object;move(a);m=bpy.data.materials.new('背景');m.diffuse_color=(.04,.05,.06,1);a.data.materials.append(m)
for loc,en in [((1,-1.4,2),55),((-1,1,1.2),65),((1,1,.5),40)]:
 bpy.ops.object.light_add(type='AREA',location=Vector(target)+Vector(loc)*span*1.8);a=bpy.context.object;a.data.energy=en*span*span;a.data.size=span*1.5;aim(a,target);move(a)
bpy.ops.object.camera_add(location=Vector(target)+Vector((1.4,-2,1.8))*span*1.8);a=bpy.context.object;a.data.type='ORTHO';a.data.ortho_scale=span*1.65;aim(a,target);sc.camera=a;move(a)
sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=False;sc.render.resolution_x=650;sc.render.resolution_y=650;sc.render.resolution_percentage=100;sc.world.color=(.2,.2,.2)
sc.render.image_settings.file_format='PNG';sc.render.filepath=os.path.join(OUT,NAME+'_预览.png')
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_location=target;area.spaces.active.region_3d.view_distance=span*2.8
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,NAME+'.blend'),compress=True);bpy.ops.render.render(write_still=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,NAME+'.blend'));o=bpy.data.objects[NAME];bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True)>0;bm.free()
open(os.path.join(OUT,'reopen_check.json'),'w').write(json.dumps({'file_reopened':True,'manifold_positive':True,'dimensions_mm':list(o.dimensions)},ensure_ascii=False,indent=2))
