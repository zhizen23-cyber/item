import bpy, math, bmesh, json, os
from mathutils import Vector
P={'diameter': 5.0, 'under_head_length': 6, 'pitch_assumed': 0.8, 'head_diameter_assumed': 8.5, 'head_height_assumed': 5.0, 'hex_af_assumed': 4.0, 'socket_depth_assumed': 2.5, 'knurl_depth_visual': 0}
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT);L=P['under_head_length'];D=P['diameter'];R=D/2;H=P['head_height_assumed'];HR=P['head_diameter_assumed']/2;TOP=L+H
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001;sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.world.color=(.25,.25,.25)
assets=bpy.data.collections.new('零件_毫米尺寸');sc.collection.children.link(assets)
preview=bpy.data.collections.new('预览专用_相机灯光地面');sc.collection.children.link(preview)
def link(o,c):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)
mat=bpy.data.materials.new('黑色外观_表面处理未确认');mat.diffuse_color=(.012,.016,.022,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.012,.016,.022,1);bs.inputs['Metallic'].default_value=.2;bs.inputs['Roughness'].default_value=.65
# Connected helical surface, not rings or a floating thread overlay.
n=144;pitch=P['pitch_assumed'];root=R-.61343*pitch;end=L;rows=[];vs=[]
steps=math.ceil(end/(pitch/20))
for j in range(steps+1):
 z=end*j/steps;ring=[]
 for i in range(n):
  a=2*math.pi*i/n;phase=(z/pitch-a/(2*math.pi))%1;dist=abs(phase-.5)
  ridge=max(0,min(1,(.4375-dist)/.3125));r=root+(R-root)*ridge
  if z<pitch*.5:r=min(r,root+z/(pitch*.5)*(R-root))
  if z>end-pitch*.5:r+=(R-r)*(z-(end-pitch*.5))/(pitch*.5)
  ring.append(len(vs));vs.append((r*math.cos(a),r*math.sin(a),z))
 rows.append(ring)
for r,z in [(R+.03*D,L),(HR-.1*D,L),(HR,L+.08*D),(HR,TOP-.1*D),(HR-.1*D,TOP)]:
 rows.append(list(range(len(vs),len(vs)+n)))
 for i in range(n):
  a=2*math.pi*i/n
  rr=r
  vs.append((rr*math.cos(a),rr*math.sin(a),z))

fs=[tuple(reversed(rows[0])),tuple(rows[-1])]
for a,b in zip(rows,rows[1:]):
 for i in range(n):fs.append((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
me=bpy.data.meshes.new(NAME);me.from_pydata(vs,[],fs);me.update();main=bpy.data.objects.new(NAME,me);assets.objects.link(main);main.data.materials.append(mat)
# Hex socket with mouth chamfer; AF is an unmeasured reference parameter.
r=P['hex_af_assumed']/math.sqrt(3);pts=[(r*math.cos(i*math.pi/3),r*math.sin(i*math.pi/3)) for i in range(6)]
v=[(x*f,y*f,z) for f,z in [(1,TOP-P['socket_depth_assumed']),(1,TOP-.12),(1.12,TOP+.02),(1.12,TOP+.2)] for x,y in pts];nn=6
f=[tuple(reversed(range(nn))),tuple(range(18,24))]+[(j*nn+i,j*nn+(i+1)%nn,(j+1)*nn+(i+1)%nn,(j+1)*nn+i) for j in range(3) for i in range(nn)]
m=bpy.data.meshes.new('槽刀');m.from_pydata(v,[],f);m.update();cut=bpy.data.objects.new('槽刀',m);assets.objects.link(cut)
bpy.context.view_layer.objects.active=main;mod=main.modifiers.new('内六角凹槽','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
bm=bmesh.new();bm.from_mesh(main.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.to_mesh(main.data);bm.free();assert bad==0 and volume>0,(bad,volume)
for p in main.data.polygons:p.use_smooth=abs(p.normal.z)<.94
for k,v in P.items():main[k]=v
main['source_photo']='../../参考照片/20261113_M5杯头与防松螺母_实物图.jpg';main['material_grade']='未确认，不推定304或强度等级'
notes='内六角圆柱头螺丝 M5×6 · 黑色杯头照片参考模型\n证据：照片隔间标签“杯头 m5*6”，可见黑色圆柱头、短螺纹与凹槽；内六角采用可见槽口及同类杯头形制参考，照片隔盖模糊，仍需实物核对。\n名义直径5mm、头下长度6mm来自标签解释，不是卡尺实测。长度按不含头解释。\n工程参考/假设：右旋M5×0.8全螺纹、头径8.5mm、头高5mm、六角对边4mm、槽深2.5mm。包络总长11mm。以上头/槽/螺距数值未在实物测量，不构成标准认证。\n黑色仅表达照片外观，材质、表面处理与强度等级未知，不推定12.9级或304。\n头侧采用光滑圆柱面，照片不足以分辨细纹。牙型、截顶、尖端、退刀过渡与倒角简化，不含制造公差。\n仅供库存识别和装配包络。精密配合及采购前需核对螺距、长度口径、头径头高、驱动槽、材料和等级。\n单位mm；原点尖端，+Z朝头部；零件与预览集合分开。build_model.py的P可修改重建。\n'+json.dumps(P,ensure_ascii=False,indent=2)
notes += '\n用户2026-11-13确认允许杯头暂按全牙建模；这不是实物全牙测量认证。\n'
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes);bpy.data.texts.new('尺寸来源与假定_请先读').write(notes)
checks={'name':NAME,'nonmanifold_edges':bad,'volume_mm3':volume,'dimensions_mm':[round(float(x),5) for x in main.dimensions],'under_head_length_mm':L,'overall_length_mm':TOP,'vertices':len(main.data.vertices)}
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(checks,indent=2,ensure_ascii=False))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
target=(0,0,TOP/2);scale=max(TOP*1.6,HR*5)
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
