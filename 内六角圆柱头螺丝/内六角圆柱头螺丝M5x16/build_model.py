import bpy, math, bmesh, json, os
from mathutils import Vector
P={'diameter': 5, 'under_head_length': 16, 'pitch_assumed': 0.8, 'head_diameter_assumed': 8.5, 'head_height_assumed': 5, 'hex_af_assumed': 4, 'socket_depth_assumed': 2.5, 'knurl_depth_visual': 0}
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT);L=P['under_head_length'];D=P['diameter'];R=D/2;H=P['head_height_assumed'];HR=P['head_diameter_assumed']/2;TOP=L+H
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.001;sc.unit_settings.length_unit='MILLIMETERS'
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=False;sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.world.color=(.25,.25,.25)
assets=bpy.data.collections.new('零件_毫米尺寸');sc.collection.children.link(assets)
preview=bpy.data.collections.new('预览专用_相机灯光地面');sc.collection.children.link(preview)
def link(o,c):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)
mat=bpy.data.materials.new('银色参考外观_订单304未实测');mat.diffuse_color=(.52,.55,.59,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.52,.55,.59,1);bs.inputs['Metallic'].default_value=.7;bs.inputs['Roughness'].default_value=.38
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
main['source_url']='https://media.distrelec.com/Web/Downloads/_t/ds/1003763_eng_tds.pdf';main['material_grade']='订单称304，未实测认证'
notes='内六角圆柱头螺丝M5x16 · 参数化名义装配模型\n来源：用户订单规格 M5×16，标题304；并非实物测量。\n名义参数：头下长度16mm，头径8.5mm，头高5mm，六角对边4mm，槽深采用表列最小值2.5mm。右旋粗牙M5×0.8，全牙版本。\n参考尺寸来源：Bossard BN3 DIN912/ISO4762全牙产品尺寸表，https://media.distrelec.com/Web/Downloads/_t/ds/1003763_eng_tds.pdf ，检索2026-11-13。仅借用标准形状尺寸，不声称用户零件为Bossard品牌、8.8级或镀锌。订单304仅作为采购文字记录，非材质认证。\n模型使用全牙版本。长规格也可能实际为半牙；当前无实物证据，需核对牙长。牙型/截顶/根部圆弧/退刀/倒角/槽口和表面纹理简化，无制造公差；槽口倒角属于展示假设。\n用途：库存识别、名义装配包络，非生产图纸或强度认证；不能用于直接加工螺纹。单位mm，原点尖端，+Z朝头。\n'+json.dumps(P,ensure_ascii=False,indent=2)
notes += '\n用户2026-11-13确认允许杯头暂按全牙建模；这不是实物全牙测量认证。\n'
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes);bpy.data.texts.new('尺寸来源与假定_请先读').write(notes)
checks={'name':NAME,'nonmanifold_edges':bad,'volume_mm3':volume,'dimensions_mm':[round(float(x),5) for x in main.dimensions],'under_head_length_mm':L,'overall_length_mm':TOP,'vertices':len(main.data.vertices)}
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(checks,indent=2,ensure_ascii=False))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
target=(0,0,TOP/2);scale=max(TOP*1.6,HR*5)
bpy.ops.mesh.primitive_plane_add(size=1000,location=(0,0,-.02));o=bpy.context.object;link(o,preview);ground=bpy.data.materials.new('Studio slate');ground.diffuse_color=(.055,.075,.1,1);o.data.materials.append(ground)
for name,loc,en,sz in [('Key',(1,-1.3,1.9),80,1),('Rim',(-1,1,1.3),110,.8),('Fill',(1.5,.5,.5),60,1)]:
 bpy.ops.object.light_add(type='AREA',location=Vector(target)+Vector(loc)*scale);o=bpy.context.object;o.name=name;o.data.energy=en*scale*scale;o.data.size=sz*scale;aim(o,target);link(o,preview)
bpy.ops.object.camera_add(location=Vector(target)+Vector((1.4,-2,1.7))*scale);cam=bpy.context.object;aim(cam,target);cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.camera=cam;link(cam,preview)
sc.render.image_settings.file_format='PNG';sc.render.filepath=os.path.join(OUT,NAME+'_预览.png')
bpy.ops.object.select_all(action='DESELECT');main.select_set(True);bpy.context.view_layer.objects.active=main
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=scale*1.5;area.spaces.active.region_3d.view_location=target
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,NAME+'.blend'),compress=True);bpy.ops.render.render(write_still=True);print('QA',checks)
