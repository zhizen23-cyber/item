import bpy, math, bmesh, json, os
from mathutils import Vector
P={'diameter':3.0,'overall_length':6,'pitch_assumed':0.5,'head_diameter_assumed':5.6,'head_height_assumed':1.65,'countersink_angle_assumed':90,'socket_width_assumed':0.72,'socket_span_assumed':2.9,'socket_depth_assumed':1.05}
OUT=os.path.dirname(os.path.abspath(__file__));NAME=os.path.basename(OUT);L=P['overall_length']
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
n=96;pitch=P['pitch_assumed'];root=1.1933;end=L-1.65;rows=[];vs=[]
steps=math.ceil(end/(pitch/20))
for j in range(steps+1):
 z=end*j/steps;ring=[]
 for i in range(n):
  a=2*math.pi*i/n;phase=(z/pitch-a/(2*math.pi))%1;dist=abs(phase-.5)
  ridge=max(0,min(1,(.4375-dist)/.3125));r=root+(1.5-root)*ridge
  if z<.23:r=min(r,1.18+z/.23*.32)
  if z>end-.2:r+=(1.5-r)*(z-(end-.2))/.2
  ring.append(len(vs));vs.append((r*math.cos(a),r*math.sin(a),z))
 rows.append(ring)
for r,z in [(1.5,L-1.45),(2.8,L-.15),(2.8,L-.035),(2.765,L)]:
 rows.append(list(range(len(vs),len(vs)+n)));vs.extend((r*math.cos(2*math.pi*i/n),r*math.sin(2*math.pi*i/n),z) for i in range(n))
fs=[tuple(reversed(rows[0])),tuple(rows[-1])]
for a,b in zip(rows,rows[1:]):
 for i in range(n):fs.append((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
me=bpy.data.meshes.new(NAME);me.from_pydata(vs,[],fs);me.update();main=bpy.data.objects.new(NAME,me);assets.objects.link(main);main.data.materials.append(mat)
# Tapered cross recess approximation. Outline is deliberately not a certified PH gauge profile.
w=P['socket_width_assumed']/2;s=P['socket_span_assumed']/2
pts=[(-w,-s),(w,-s),(w,-w),(s,-w),(s,w),(w,w),(w,s),(-w,s),(-w,w),(-s,w),(-s,-w),(-w,-w)]
v=[(x*f,y*f,z) for f,z in [(.52,L-P['socket_depth_assumed']),(1,L+.15)] for x,y in pts];nn=len(pts)
f=[tuple(reversed(range(nn))),tuple(range(nn,2*nn))]+[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)]
m=bpy.data.meshes.new('槽刀');m.from_pydata(v,[],f);m.update();cut=bpy.data.objects.new('槽刀',m);assets.objects.link(cut)
bpy.context.view_layer.objects.active=main;mod=main.modifiers.new('十字凹槽','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
bm=bmesh.new();bm.from_mesh(main.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.to_mesh(main.data);bm.free();assert bad==0 and volume>0,(bad,volume)
for p in main.data.polygons:p.use_smooth=abs(p.normal.z)<.94
for k,v in P.items():main[k]=v
main['source_photo']='../M3x4与M3x6_共用实物图.jpg';main['material_grade']='未确认，不推定304或强度等级'
notes=f'''十字沉头螺丝 M3×{int(L)} · 照片参考模型
照片两格明确标 3*6 和 3*4。当前文件只含 M3×{int(L)} 一种规格，另一规格单独保存。
由可见平头、锥形底面及十字凹槽判断为十字沉头螺丝。总长按沉头螺钉惯例含头解释；不是头下长度。标签本身未给标准号。
螺纹按常用 M3×0.5 右旋建立连续螺旋近似牙形，不是独立圆环。未加入制造公差、滚丝牙根圆角或螺纹量规认证。
头径 5.6、头高 1.65、90° 沉头参照供应商同类产品数据；十字槽宽/深、倒角为估计，不能凭照片确认标准、材质或等级。并未认定用户实物就是该供应商型号。
参考： https://www.ettinger.de/en/product-datasheet/7f6af7fb5171cc50c9ad23da4012b5ab/create
使用前请实测外径、含头总长、头径、头高、螺距与驱动槽；本文件用于库存识别和布局预览，不是可直接加工的认证图。
单位 mm；零件与预览集合分开。两个规格共用父目录实物 JPG。
修改 P 后运行 blender -b --python build_model.py 可重建，注意备份自定义修改。
'''+json.dumps(P,ensure_ascii=False,indent=2)
open(os.path.join(OUT,'模型说明.txt'),'w').write(notes);bpy.data.texts.new('尺寸来源与假定_请先读').write(notes)
checks={'name':NAME,'nonmanifold_edges':bad,'volume_mm3':volume,'dimensions_mm':[round(float(x),5) for x in main.dimensions],'overall_length_mm':L,'vertices':len(main.data.vertices)}
open(os.path.join(OUT,'geometry_check.json'),'w').write(json.dumps(checks,indent=2,ensure_ascii=False))
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
target=(0,0,L/2);scale=9.8
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
