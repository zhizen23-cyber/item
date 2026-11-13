import bpy, math, bmesh, json, os
from mathutils import Vector
P={'diameter_nominal':3.5,'overall_length_nominal':8,'pitch_assumed':0.6,'head_diameter_assumed':7.0,'head_height_assumed':2.0,'socket_max_diameter_assumed':2.8,'socket_min_diameter_assumed':2.0,'socket_depth_assumed':1.15}
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT);TOP=P['overall_length_nominal'];L=TOP-P['head_height_assumed']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001;sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.world.color=(.25,.25,.25)
assets=bpy.data.collections.new('零件_毫米尺寸');sc.collection.children.link(assets)
preview=bpy.data.collections.new('预览专用_相机灯光地面');sc.collection.children.link(preview)
def link(o,c):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)
mat=bpy.data.materials.new('黑色表面_处理方式未核实');mat.diffuse_color=(.055,.065,.08,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.055,.065,.08,1);bs.inputs['Metallic'].default_value=.35;bs.inputs['Roughness'].default_value=.55
# Closed single surface: helical shank, countersink, six-lobe socket.
n=144;pitch=P['pitch_assumed'];major=1.75;root=major-.61343*pitch;end=L;rows=[];vs=[]
def ring(z,fn):
 ids=[]
 for i in range(n):
  a=2*math.pi*i/n;r=fn(a);ids.append(len(vs));vs.append((r*math.cos(a),r*math.sin(a),z))
 rows.append(ids)
steps=math.ceil(end/(pitch/24))
for j in range(steps+1):
 z=end*j/steps
 def rad(a):
  phase=(z/pitch-a/(2*math.pi))%1;dist=abs(phase-.5)
  ridge=max(0,min(1,(.4375-dist)/.3125));r=root+(major-root)*ridge
  if z<.22:r=min(r,major-.22+z)
  if z>end-.18:r+=(major-r)*(z-(end-.18))/.18
  return r
 ring(z,rad)
# Assumed 90-degree cone, short rim and edge bevel, not certified dimensions.
for rr,z in [(3.5,L+1.75),(3.5,TOP-.1),(3.4,TOP)]:ring(z,lambda a,r=rr:r)
# Six lobes are a visual approximation, not standardized Torx tool geometry.
for fac,z in [(1.05,TOP),(1,TOP-.1),(1,TOP-P['socket_depth_assumed'])]:
 ring(z,lambda a,f=fac:f*(1.2+.2*math.cos(6*a)))
fs=[tuple(reversed(rows[0])),tuple(rows[-1])]
for a,b in zip(rows,rows[1:]):
 for i in range(n):fs.append((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
me=bpy.data.meshes.new(NAME);me.from_pydata(vs,[],fs);me.update();main=bpy.data.objects.new(NAME,me);assets.objects.link(main);main.data.materials.append(mat)
bm=bmesh.new();bm.from_mesh(main.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.to_mesh(main.data);bm.free();assert bad==0 and volume>0,(bad,volume)
for p in main.data.polygons:p.use_smooth=abs(p.normal.z)<.94
for k,v in P.items():main[k]=v
main['source_photo']='../../参考照片/20261113_圆柱头与梅花沉头螺丝_实物图.jpg';main['material_grade']='12.9级来自标签及用户描述；未验证材质、硬度和认证'
notes='12.9级梅花沉头螺丝 M3.5×8 · 可编辑照片概念模型\n证据来源：空格标签 M3.5×8 12.9；用户说明已用完、与右下角12mm同款仅长度8mm，梅花头倒角。没有8mm实物可直接核对。\n长度解释：沉头螺丝名义长度通常含头，本模型总长8mm；用户未提供测量，需确认长度口径。\n名义直径3.5mm来自标签。右旋螺距0.6mm是M3.5粗牙参考假设，不是实测。\n外观假设：头径7.0mm、头高2.0mm、90°锥面、顶缘小倒角，六瓣槽最大径2.8mm最小径2.0mm深1.15mm。\n六瓣槽使用连续余弦轮廓视觉近似，不是标准Torx轮廓，不指定T号或保证工具配合。头径、头高、螺距、槽号均待卡尺/牙规/批头核实。\n12.9级为标签与用户提供的等级描述，本模型不验证硬度或材料证书；黑色材质仅表达照片外观，不推断发黑/镀层工艺。\n螺纹牙形、截顶、端部倒角及头下过渡已简化，无公差。仅用于库存识别/布局，不作为制造、强度验证或采购配合依据。\n单位mm，原点尖端，+Z朝头部。模型与预览集合分离。build_model.py可重建。\n'+json.dumps(P,ensure_ascii=False,indent=2)
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes);bpy.data.texts.new('尺寸来源与假定_请先读').write(notes)
checks={'name':NAME,'nonmanifold_edges':bad,'volume_mm3':volume,'dimensions_mm':[round(float(x),5) for x in main.dimensions],'shank_to_cone_start_mm':L,'overall_length_mm':TOP,'vertices':len(main.data.vertices)}
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(checks,indent=2,ensure_ascii=False))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
target=(0,0,TOP/2);scale=17
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
