import bpy, math, bmesh, json, os
from mathutils import Vector
P={'nominal_diameter':5,'across_flats_assumed':8,'height_assumed':5,'pitch_assumed':.8,'insert_material':'未知_仅示意','insert_outer_radius_assumed':3.05,'insert_inner_radius_assumed':2.35}
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT);L=P['height_assumed'];D=P['nominal_diameter'];AF=P['across_flats_assumed'];pitch=P['pitch_assumed']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001;sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.world.color=(.25,.25,.25)
assets=bpy.data.collections.new('零件_毫米尺寸');sc.collection.children.link(assets)
preview=bpy.data.collections.new('预览专用_相机灯光地面');sc.collection.children.link(preview)
def link(o,c):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)
mat=bpy.data.materials.new('黑色金属外观_材质涂层未确认');mat.diffuse_color=(.055,.065,.08,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.055,.065,.08,1);bs.inputs['Metallic'].default_value=.9;bs.inputs['Roughness'].default_value=.3
# One closed annular mesh: a hexagonal outside and continuous helical inside.
n=192;vs=[];rows=[]
def ring(z,radii):
 row=[]
 for i,r in enumerate(radii):
  a=2*math.pi*i/n;row.append(len(vs));vs.append((r*math.cos(a),r*math.sin(a),z))
 rows.append(row)
def hexr(a):return AF/2/math.cos((a%(math.pi/3))-math.pi/6)
# Outer hex edge chamfer is simplified, not a measured turned profile.
for z,shrink in [(0,.25),(.25,0),(3.45,0),(3.7,.25)]:
 ring(z,[hexr(2*math.pi*i/n)-shrink for i in range(n)])
# Raised metal collar surrounding the illustrative locking insert.
for z,r in [(3.7,3.75),(4.75,3.75),(5,3.5),(5,2.85),(4.85,3.12),(3.6,3.12),(3.55,D/2+.08)]:ring(z,[r]*n)
steps=math.ceil(3.55/pitch*28)
for j in range(steps+1):
 z=3.55*(1-j/steps);rs=[]
 for i in range(n):
  a=2*math.pi*i/n;phase=(z/pitch-a/(2*math.pi))%1
  shape=max(0,min(1,(.4375-abs(phase-.5))/.3125))
  r=D/2-.541266*pitch+.541266*pitch*shape
  mouth=max(0,1-min(z,3.55-z)/(.55*pitch));r=r*(1-mouth)+(D/2+.08)*mouth;rs.append(r)
 ring(z,rs)
fs=[]
for a,b in zip(rows,rows[1:]+rows[:1]):
 for i in range(n):fs.append((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
me=bpy.data.meshes.new(NAME);me.from_pydata(vs,[],fs);me.update();main=bpy.data.objects.new(NAME,me);assets.objects.link(main);main.data.materials.append(mat)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.to_mesh(me);bm.free();assert bad==0 and vol>0
for f in me.polygons:f.use_smooth=(4*n <= f.index < len(me.polygons)-n)
for k,v in P.items():main[k]=v
# Separate illustrative insert, with clearance from metal pocket.
iv=[];inf=[]
for z,r in [(3.65,3.05),(4.8,3.05),(4.8,2.35),(3.65,2.35)]:
 for i in range(n):
  a=2*math.pi*i/n;iv.append((r*math.cos(a),r*math.sin(a),z))
for j in range(4):
 for i in range(n):inf.append((j*n+i,j*n+(i+1)%n,((j+1)%4)*n+(i+1)%n,((j+1)%4)*n+i))
im=bpy.data.meshes.new('内衬示意网格');im.from_pydata(iv,[],inf);im.update();insert=bpy.data.objects.new('环形内衬_材料与构造未确认_示意',im);assets.objects.link(insert)
bm=bmesh.new();bm.from_mesh(im);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));ibad=sum(not e.is_manifold for e in bm.edges);ivol=bm.calc_volume(signed=True);bm.to_mesh(im);bm.free();assert ibad==0 and ivol>0
imat=bpy.data.materials.new('环形内衬_颜色仅示意_材质未知');imat.diffuse_color=(.13,.15,.18,1);imat.use_nodes=True;ibs=imat.node_tree.nodes.get('Principled BSDF');ibs.inputs['Base Color'].default_value=(.13,.15,.18,1);ibs.inputs['Roughness'].default_value=.48;im.materials.append(imat)
for f in im.polygons:f.use_smooth=abs(f.normal.z)<.8
main['source_photo']='../../参考照片/20261113_M5杯头与防松螺母_实物图.jpg'
notes='防松螺母 M5 · 照片参考/内部构造示意模型\n照片标签提供M5防松螺母，可见黑色六角本体与上口环形结构。无实测标尺，未确认具体标准、材料、涂层、强度等级及锁紧方式。\n参考假设：M5右旋粗牙0.8mm、六角对边8mm、总高5mm；六角体高3.7mm，上部圆形包边外径7.5mm，口径5.7mm。以上均非实测。\n独立对象“环形内衬_材料与构造未确认_示意”用来表示照片环形内层，不认定为尼龙。外径6.1mm、内径4.7mm、高1.15mm，位置z3.65至4.8mm均为构造示意假设，不能作为防松性能或可制造性证明。\n金属内螺纹只在下部呈现，内衬为光滑环，不模拟螺纹切入、弹性变形、摩擦或锁紧力矩。未认证DIN985等标准。\n倒角与牙形简化，无加工公差或量规验证。原点下表面中心，+Z轴向，mm单位。采购/装配需先核对螺距、外形尺寸及真实防松结构。\n可编辑模型分金属本体和环形内衬，预览对象独立集合。修改P和轮廓参数后可用blender -b --python build_model.py重建。\n'+json.dumps(P,ensure_ascii=False,indent=2)
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes);bpy.data.texts.new('尺寸依据与边界').write(notes)
checks={'name':NAME,'nonmanifold_edges':bad,'volume_mm3':vol,'dimensions_mm':list(main.dimensions),'reference_assumptions':P,'insert_nonmanifold_edges':ibad,'insert_volume_mm3':ivol}
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(checks,ensure_ascii=False,indent=2))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
target=(0,0,L/2);scale=AF*1.65
bpy.ops.mesh.primitive_plane_add(size=100,location=(0,0,-.02));o=bpy.context.object;link(o,preview);ground=bpy.data.materials.new('Studio slate');ground.diffuse_color=(.055,.075,.1,1);o.data.materials.append(ground)
for name,loc,en,sz in [('Key',(1,-1.3,1.9),80,1),('Rim',(-1,1,1.3),110,.8),('Fill',(1.5,.5,.5),60,1)]:
 bpy.ops.object.light_add(type='AREA',location=Vector(target)+Vector(loc)*scale);o=bpy.context.object;o.name=name;o.data.energy=en*scale*scale;o.data.size=sz*scale;aim(o,target);link(o,preview)
bpy.ops.object.camera_add(location=Vector(target)+Vector((1.4,-2,1.7))*scale);cam=bpy.context.object;aim(cam,target);cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.camera=cam;link(cam,preview)
sc.render.image_settings.file_format='PNG';sc.render.filepath=os.path.join(OUT,NAME+'_预览.png')
bpy.ops.object.select_all(action='DESELECT');main.select_set(True);bpy.context.view_layer.objects.active=main
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=scale*1.5;area.spaces.active.region_3d.view_location=target
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,NAME+'.blend'),compress=True);bpy.ops.render.render(write_still=True);print('QA',checks)
