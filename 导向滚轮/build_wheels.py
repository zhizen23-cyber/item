import bpy,math,os,json,bmesh
from mathutils import Vector
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(n,c,metal=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.28;return m
white=mat('白色轮体_材料未标注',(.8,.82,.84));steel=mat('轴承芯占位_内部未知',(.27,.29,.33),.8)
def lathe(n,profile,m):
 # axial Y, profile vertices (radius, axial), editable closed outline + live Screw modifier
 me=bpy.data.meshes.new(n+'_截面');me.from_pydata([(r,y,0)for y,r in profile],[(i,(i+1)%len(profile))for i in range(len(profile))],[]);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);o.data.materials.append(m)
 md=o.modifiers.new('可编辑截面_绕Y旋转','SCREW');md.axis='Y';md.angle=2*math.pi;md.steps=96;md.render_steps=128;md.use_merge_vertices=True;md.use_smooth_shade=True;return o
specs=[dict(id='W01',name='小平轮_D15p3_W8p8_孔5',D=15.3,W=8.8,bore=5,flat=6,profile=[(-4.4,6.25),(-3,7.65),(3,7.65),(4.4,6.25)],coreR=5.1,unknown='45°肩部倒角由示意推定；内部轴承型号/内圈宽度/钢芯外径未标注'),dict(id='W02',name='大平轮_D24p1_W11_孔5',D=24.1,W=11,bore=5,profile=[(-5.5,10.25),(-3.7,12.05),(3.7,12.05),(5.5,10.25)],coreR=8,unknown='侧倒角1.8mm为外观占位，非图中标注；内部轴承/钢芯直径未知'),dict(id='W03',name='V轮_D24p4_W11_孔5',D=24.4,W=11,bore=5,groove_width=5.5,groove_depth_approx=2,profile=[(-5.5,10.2),(-2.75,12.2),(0,10.2),(2.75,12.2),(5.5,10.2)],coreR=8,unknown='槽深约2mm按近似值；外侧倒角/槽底圆角未标注；内部轴承未知')]
for k,sp in enumerate(specs):
 coll=bpy.data.collections.new(sp['name']);bpy.context.scene.collection.children.link(coll)
 root=bpy.data.objects.new(sp['name']+'_参数',None);coll.objects.link(root)
 for a,v in sp.items():
  if a!='profile':root[a]=v
 w=sp['W'];R=sp['coreR'];body=lathe(sp['id']+'_白轮体_截面可编辑',[(-w/2,R)]+sp['profile']+[(w/2,R)],white);core=lathe(sp['id']+'_钢芯仅包络_非轴承内部',[(-w/2,2.5),(-w/2,R),(w/2,R),(w/2,2.5)],steel)
 for o in [body,core]:
  for c in list(o.users_collection):c.objects.unlink(o)
  coll.objects.link(o);o.parent=root;o['用途']='外形与装配包络，不是内部轴承制造图';o['未知']=sp['unknown']
 # library write only this collection to standalone blend, plus parameters/text.
 root.location=(0,0,0)
 bpy.data.libraries.write(OUT+'/'+sp['name']+'.blend',{coll},fake_user=False,compress=True)
 root.location.x=(k-1)*36
 # label retained in comparison only
 bpy.ops.object.text_add(location=((k-1)*36,-15,-12));txt=bpy.context.object;txt.data.body=f"D{sp['D']} / W{sp['W']} / ID5";txt.data.size=3;txt.data.align_x='CENTER';txt.rotation_euler=(math.pi/2,0,0)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001;s.render.engine='CYCLES';s.cycles.samples=32;s.render.resolution_x=1400;s.render.resolution_y=750;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX'
w=bpy.data.worlds.new('轮模型灯光');s.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.23,.23,.23,1);w.node_tree.nodes['Background'].inputs[1].default_value=.7
for p,e in [((0,-60,90),100000),((50,30,50),70000)]:
 bpy.ops.object.light_add(type='AREA',location=p);o=bpy.context.object;o.data.energy=e;o.data.size=80;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(65,-130,70));c=bpy.context.object;c.rotation_euler=(Vector((0,0,0))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=125;s.camera=c
for scr in bpy.data.screens:
 for a in scr.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_location=(0,0,0);a.spaces.active.region_3d.view_distance=150;a.spaces.active.region_3d.view_rotation=c.rotation_euler.to_quaternion();a.spaces.active.shading.color_type='MATERIAL'
json.dump(specs,open(OUT+'/三轮规格与未知项.json','w'),ensure_ascii=False,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/三种实轮_可编辑截面对照.blend',compress=True);s.render.filepath=OUT+'/三轮外形预览.png';bpy.ops.render.render(write_still=True)
