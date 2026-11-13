import bpy,bmesh,math,json,os
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001;s.unit_settings.length_unit='MILLIMETERS';s.frame_end=240
parts=bpy.data.collections.new('零件_1单位1毫米');s.collection.children.link(parts)
def mat(n,c,metal=.8):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=.3;return m
black=mat('黑色表面',(.065,.075,.09));steel=mat('钢轨',(.42,.47,.53));poly=mat('缓冲器示意',(.77,.79,.73),0);rubber=mat('释放拨片',(.025,.03,.035),0)
def add(n,verts,faces,m,parent=None):
 me=bpy.data.meshes.new(n);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(n,me);parts.objects.link(o);o.data.materials.append(m)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o.parent=parent;return o
def prism(n,p,x0,l,m,parent=None):
 N=len(p);v=[(x,y,z) for x in [x0,x0+l] for y,z in p];f=[tuple(reversed(range(N))),tuple(range(N,N*2))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)];return add(n,v,f,m,parent)
def box(n,x,y,z,l,w,h,m,parent=None):return prism(n,[(y,z),(y+w,z),(y+w,z+h),(y,z+h)],x,l,m,parent)
def root(n):o=bpy.data.objects.new(n,None);parts.objects.link(o);return o
fixed=root('固定外轨');mid=root('中轨_示意位移200');inner=root('内轨_示意位移400')
# Actual hole placement is unknown: intentionally omit all fixing holes rather than invent a drill template.
prism('外轨_45mm高度暂估_无定位孔',[(0,0),(10,0),(10,1.1),(1.1,1.1),(1.1,43.9),(10,43.9),(10,45),(0,45)],0,400,black,fixed)
prism('中轨_截面暂估',[(3,5),(9,5),(9,6),(4,6),(4,39),(9,39),(9,40),(3,40)],5,390,steel,mid)
prism('内轨_截面暂估',[(12.7,12),(6,12),(6,13),(11.6,13),(11.6,32),(6,32),(6,33),(12.7,33)],0,400,black,inner)
box('阻尼壳体_外观示意',8,1.2,15,100,1.5,15,poly,fixed)
box('阻尼缸_不代表内部行程',15,2.8,20,45,2,5,rubber,fixed)
box('阻尼杆_静态示意',60,3.3,22,38,1,1,steel,fixed)
box('拆卸拨片_不代表卡扣机构',330,8,20,45,2,5,rubber,inner)
for parent,travel in [(mid,200),(inner,400)]:
 for fr,x in [(1,0),(30,0),(100,travel),(135,travel),(210,0),(240,0)]:parent.location.x=x;parent.keyframe_insert(data_path='location',frame=fr)
 for fc in parent.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='BEZIER'
for fr,label in [(1,'收回'),(100,'完全伸出_内轨400mm'),(210,'回收')]:s.timeline_markers.new(label,frame=fr)
notes='''DTC 45871H 16寸/400mm 三节阻尼滑轨：运动包络参考，不是复刻工程图。
来源：用户产品图1000023357.png。已确认：公称长度400mm、拉出长度400mm、厚12.7mm、双边安装预留26mm、冷轧钢；45kg是商品页宣称，不是本模型验证。
未确认：截面高度（本模型暂取45mm）、各节截面/板厚/长度、定位孔与端孔、滚珠数量/滚道、阻尼器内部与卡扣。未采用此前500mm版本孔位，也未等比缩放它。为避免误当钻孔图，本文件故意不建定位孔。应以实物卡尺或对应型号官方尺寸图补充。
X轴为收放方向，Y厚度，Z高度。1 Blender单位=1mm。仅建一条导轨，左右安装预留26mm不等于本模型单条厚度26mm。
动画1-240帧：中轨0到200mm、内轨0到400mm后回收；这是展示用分配，不是实测顺序、阻尼或滚珠运动解算。外轨固定。闭合总体400×12.7×45(高为暂估)，全伸出总包络800mm。
不得直接用于加工、孔位定位、载荷认证、碰撞保证或阻尼/回弹计算。无真实物理机构约束。商品图本身不足以验证全部配合。
运行：blender -b --python build_model.py。同目录交付文件会覆盖，请备份。
'''
open(OUT+'/模型说明.txt','w').write(notes);bpy.data.texts.new('必读_尺寸依据与未确认项目').write(notes)
open(OUT+'/README.md','w').write('# '+NAME+'\n\n![预览]('+NAME+'_预览.png)\n\n'+notes+'\n[Blender模型]('+NAME+'.blend)\n')
checks=[]
for o in parts.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);vol=bm.calc_volume(signed=True);bm.free();assert bad==0 and vol>0;checks.append(dict(object=o.name,nonmanifold=bad,volume_mm3=vol))
states=[]
for frame,length in [(1,400),(100,800),(210,400)]:
 s.frame_set(frame);bpy.context.view_layer.update();pts=[o.matrix_world@Vector(p) for o in parts.objects if o.type=='MESH' for p in o.bound_box];dims=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)];assert abs(dims[0]-length)<1e-5;assert abs(dims[1]-12.7)<1e-4;states.append(dict(frame=frame,envelope_mm=dims))
open(OUT+'/geometry_check.json','w').write(json.dumps(dict(parts=checks,states=states,height_is_assumed=True,holes='intentionally omitted; unknown',physics_validated=False),ensure_ascii=False,indent=2))
# Studio framing: partially extended preview makes all three members legible.
s.frame_set(65);s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False;s.render.resolution_x=1200;s.render.resolution_y=650;s.render.resolution_percentage=100;s.world.color=(.3,.3,.3)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
preview=bpy.data.collections.new('预览_非零件');s.collection.children.link(preview)
def rehome(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 preview.objects.link(o)
bpy.ops.mesh.primitive_plane_add(size=4000,location=(300,0,-1));o=bpy.context.object;rehome(o);o.data.materials.append(mat('背景',(.045,.065,.09),0))
for loc,energy in [((200,-400,650),22000000),((500,300,450),26000000),((-200,100,250),12000000)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;rehome(o);o.data.energy=energy;o.data.size=450;aim(o,(300,0,20))
bpy.ops.object.camera_add(location=(450,900,700));cam=bpy.context.object;rehome(cam);aim(cam,(300,4,20));cam.data.clip_end=10000;cam.data.type='ORTHO';cam.data.ortho_scale=900;s.camera=cam
s.render.image_settings.file_format='PNG';s.render.filepath=OUT+'/'+NAME+'_预览.png'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='DESELECT');inner.select_set(True);bpy.context.view_layer.objects.active=inner
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=750;area.spaces.active.region_3d.view_location=(300,0,20)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/'+NAME+'.blend',compress=True);bpy.ops.render.render(write_still=True)
