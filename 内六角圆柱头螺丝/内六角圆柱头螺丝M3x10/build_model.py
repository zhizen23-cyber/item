import bpy, math, bmesh, json, os
from mathutils import Vector
P={'diameter': 3, 'under_head_length': 10, 'pitch_assumed': 0.5, 'head_diameter_assumed': 5.5, 'head_height_assumed': 3, 'hex_af_assumed': 2.5, 'socket_depth_assumed': 1.3, 'knurl_depth_visual': 0.06, 'knurl_count_visual': 48}
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT);L=P['under_head_length'];D=P['diameter'];R=D/2;H=P['head_height_assumed'];HR=P['head_diameter_assumed']/2;TOP=L+H
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
  rr=r-(P['knurl_depth_visual']*(.5-.5*math.cos(P['knurl_count_visual']*a)) if L+.05*D<z<TOP-.05*D else 0)
  vs.append((rr*math.cos(a),rr*math.sin(a),z))

fs=[tuple(reversed(rows[0])),tuple(rows[-1])]
for a,b in zip(rows,rows[1:]):
 for i in range(n):fs.append((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
me=bpy.data.meshes.new(NAME);me.from_pydata(vs,[],fs);me.update();main=bpy.data.objects.new(NAME,me);assets.objects.link(main);main.data.materials.append(mat)
# True hexagonal recess; slight mouth chamfer, nominal AF 1.5 mm.
r=P['hex_af_assumed']/math.sqrt(3);pts=[(r*math.cos(i*math.pi/3),r*math.sin(i*math.pi/3)) for i in range(6)]
v=[(x*f,y*f,z) for f,z in [(1,TOP-P['socket_depth_assumed']),(1,TOP-.12),(1.12,TOP+.02),(1.12,TOP+.2)] for x,y in pts];nn=6
f=[tuple(reversed(range(nn))),tuple(range(18,24))]+[(j*nn+i,j*nn+(i+1)%nn,(j+1)*nn+(i+1)%nn,(j+1)*nn+i) for j in range(3) for i in range(nn)]
m=bpy.data.meshes.new('槽刀');m.from_pydata(v,[],f);m.update();cut=bpy.data.objects.new('槽刀',m);assets.objects.link(cut)
bpy.context.view_layer.objects.active=main;mod=main.modifiers.new('内六角凹槽','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
bm=bmesh.new();bm.from_mesh(main.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.to_mesh(main.data);bm.free();assert bad==0 and volume>0,(bad,volume)
for p in main.data.polygons:p.use_smooth=abs(p.normal.z)<.94
for k,v in P.items():main[k]=v
main['source_photo']='../../参考照片/20261113_M3杯头螺丝_实物图.jpg';main['material_grade']='未确认，不推定304或强度等级'
notes='内六角圆柱头螺丝 M3×10 · 照片参考模型\n证据：隔间标签 m3*10，杯头/内六角来自标签和可见头部。名义直径3mm和长度10mm来自标签，非实测。长度暂按头下长度解释。\nM3×10与M3×14照片能辨圆柱头六角凹槽及侧直纹；M3×16被标签和隔板遮挡较多、M3×25部分头部细节遮挡，同类槽型和侧直纹有推定成分。\n参考假设：右旋全螺纹，螺距0.5mm、头径5.5mm、头高3mm、内六角对边2.5mm、槽深1.3mm。48条深0.06mm侧直纹为视觉近似。所有头槽与牙型尺寸均非实测，未认证DIN/ISO标准。\n总包络长13mm。材质、镀层和强度等级未知，不推定304或12.9级。银色仅为外观。\n螺纹、倒角、退刀过渡与平端简化，无制造公差或量规验证，不能据此直接制造或认定匹配。\n单位mm，原点尖端，+Z朝头部；零件与预览集合分开。用于库存识别/布局，采购配合前请核对螺距、头下长、头径高、内六角与材料。\n修改P后以blender -b --python build_model.py重建。\n'+json.dumps(P,ensure_ascii=False,indent=2)
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes);bpy.data.texts.new('尺寸来源与假定_请先读').write(notes)
checks={'name':NAME,'nonmanifold_edges':bad,'volume_mm3':volume,'dimensions_mm':[round(float(x),5) for x in main.dimensions],'under_head_length_mm':L,'overall_length_mm':TOP,'vertices':len(main.data.vertices)}
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(checks,indent=2,ensure_ascii=False))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
target=(0,0,TOP/2);scale=max(TOP*1.6,HR*5)
bpy.ops.mesh.primitive_plane_add(size=500,location=(0,0,-.02));o=bpy.context.object;link(o,preview);ground=bpy.data.materials.new('Studio slate');ground.diffuse_color=(.055,.075,.1,1);o.data.materials.append(ground)
for name,loc,en,sz in [('Key',(1,-1.3,1.9),80,1),('Rim',(-1,1,1.3),110,.8),('Fill',(1.5,.5,.5),60,1)]:
 bpy.ops.object.light_add(type='AREA',location=Vector(target)+Vector(loc)*scale);o=bpy.context.object;o.name=name;o.data.energy=en*scale*scale;o.data.size=sz*scale;aim(o,target);link(o,preview)
bpy.ops.object.camera_add(location=Vector(target)+Vector((1.4,-2,1.7))*scale);cam=bpy.context.object;aim(cam,target);cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.camera=cam;link(cam,preview)
sc.render.image_settings.file_format='PNG';sc.render.filepath=os.path.join(OUT,NAME+'_预览.png')
bpy.ops.object.select_all(action='DESELECT');main.select_set(True);bpy.context.view_layer.objects.active=main
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=scale*1.5;area.spaces.active.region_3d.view_location=target
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,NAME+'.blend'),compress=True);bpy.ops.render.render(write_still=True);print('QA',checks)
