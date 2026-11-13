import bpy, math, bmesh, json, os
from mathutils import Vector
P={'diameter':2.0,'under_head_length':5,'pitch_assumed':0.4,'head_diameter_assumed':3.8,'head_height_assumed':2.0,'hex_af_assumed':1.5,'socket_depth_assumed':1.0,'knurl_depth_visual':0.045}
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT);L=P['under_head_length'];TOP=L+2
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001;sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.world.color=(.25,.25,.25)
assets=bpy.data.collections.new('零件_毫米尺寸');sc.collection.children.link(assets)
preview=bpy.data.collections.new('预览专用_相机灯光地面');sc.collection.children.link(preview)
def link(o,c):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)
mat=bpy.data.materials.new('银色金属_材质牌号未确认');mat.diffuse_color=(.52,.57,.62,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.52,.57,.62,1);bs.inputs['Metallic'].default_value=.9;bs.inputs['Roughness'].default_value=.26
# Connected helical surface, not rings or a floating thread overlay.
n=144;pitch=P['pitch_assumed'];root=.7546;end=L;rows=[];vs=[]
steps=math.ceil(end/(pitch/20))
for j in range(steps+1):
 z=end*j/steps;ring=[]
 for i in range(n):
  a=2*math.pi*i/n;phase=(z/pitch-a/(2*math.pi))%1;dist=abs(phase-.5)
  ridge=max(0,min(1,(.4375-dist)/.3125));r=root+(1.0-root)*ridge
  if z<.23:r=min(r,.76+z/.23*.24)
  if z>end-.2:r+=(1.0-r)*(z-(end-.2))/.2
  ring.append(len(vs));vs.append((r*math.cos(a),r*math.sin(a),z))
 rows.append(ring)
for r,z in [(1.08,L),(1.8,L),(1.9,L+.1),(1.9,L+1.8),(1.75,TOP)]:
 rows.append(list(range(len(vs),len(vs)+n)))
 for i in range(n):
  a=2*math.pi*i/n
  rr=r-(.045*(.5-.5*math.cos(48*a)) if L+.05<z<L+1.85 else 0)
  vs.append((rr*math.cos(a),rr*math.sin(a),z))

fs=[tuple(reversed(rows[0])),tuple(rows[-1])]
for a,b in zip(rows,rows[1:]):
 for i in range(n):fs.append((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
me=bpy.data.meshes.new(NAME);me.from_pydata(vs,[],fs);me.update();main=bpy.data.objects.new(NAME,me);assets.objects.link(main);main.data.materials.append(mat)
# True hexagonal recess; slight mouth chamfer, nominal AF 1.5 mm.
r=P['hex_af_assumed']/math.sqrt(3);pts=[(r*math.cos(i*math.pi/3),r*math.sin(i*math.pi/3)) for i in range(6)]
v=[(x*f,y*f,z) for f,z in [(1,TOP-1),(1,TOP-.12),(1.12,TOP+.02),(1.12,TOP+.2)] for x,y in pts];nn=6
f=[tuple(reversed(range(nn))),tuple(range(18,24))]+[(j*nn+i,j*nn+(i+1)%nn,(j+1)*nn+(i+1)%nn,(j+1)*nn+i) for j in range(3) for i in range(nn)]
m=bpy.data.meshes.new('槽刀');m.from_pydata(v,[],f);m.update();cut=bpy.data.objects.new('槽刀',m);assets.objects.link(cut)
bpy.context.view_layer.objects.active=main;mod=main.modifiers.new('内六角凹槽','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
bm=bmesh.new();bm.from_mesh(main.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.to_mesh(main.data);bm.free();assert bad==0 and volume>0,(bad,volume)
for p in main.data.polygons:p.use_smooth=abs(p.normal.z)<.94
for k,v in P.items():main[k]=v
main['source_photo']='../M2x5与M2x10_补充实物图.jpg';main['material_grade']='未确认，不推定304或强度等级'
notes=f"""内六角圆柱头螺丝 M2×{int(L)} · 照片参考模型
照片标签为 m2*10 与 m2*5，分别建模。当前为 M2×{int(L)}。
长度按圆柱头螺钉头下长度解释；头高参考2 mm，因此总包络为 {L+2} mm。
M2×0.4右旋全螺纹、头径3.8 mm、头高2 mm、内六角对边1.5 mm、槽深1 mm为同类标准件参考值，不是用户实物的测量值。
参考供应商规格：https://www.accu.co.uk/metric-cap-head-screws/3789-SSCF-M2-3-A2
该参考页面是M2×3，仅用于M2头型/螺距，用户长度来自标签5/10。未认定用户实物的DIN/ISO标准、材质或强度等级。
照片可见头侧滚花；本模型48条浅直纹为视觉近似，纹数和深度未实测。倒角、牙形截顶、退刀过渡为简化；没有加工公差或量规认证。
原点在螺丝尖端中心，+Z朝头部，单位mm。零件与预览集合分开。
适合库存识别和布局，精密配合/采购/制造前需实测螺距、头下长度、头径、头高、六角槽与材料等级。
修改P后运行blender -b --python build_model.py重建，注意保存原有修改。
"""+json.dumps(P,ensure_ascii=False,indent=2)
notes += '\n用户2026-11-13确认允许杯头暂按全牙建模；这不是实物全牙测量认证。\n'
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes);bpy.data.texts.new('尺寸来源与假定_请先读').write(notes)
checks={'name':NAME,'nonmanifold_edges':bad,'volume_mm3':volume,'dimensions_mm':[round(float(x),5) for x in main.dimensions],'under_head_length_mm':L,'overall_length_mm':TOP,'vertices':len(main.data.vertices)}
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(checks,indent=2,ensure_ascii=False))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
target=(0,0,TOP/2);scale=15.5
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
