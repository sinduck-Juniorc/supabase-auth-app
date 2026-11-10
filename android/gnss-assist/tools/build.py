"""Python 3.11 + JDK 17 이상 + Android SDK 35. 외부 Gradle 의존성 없는 진단 APK 빌드."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, zipfile, platform, sys
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--sdk',type=Path,required=True);p.add_argument('--keystore',type=Path,required=True);args=p.parse_args()
build=root/'build';build.mkdir(exist_ok=True);classes=build/'classes';classes.mkdir(exist_ok=True);dex=build/'dex';dex.mkdir(exist_ok=True)
sdk=args.sdk.resolve();bt=sdk/'build-tools/35.0.0';jar=sdk/'platforms/android-35/android.jar';windows=os.name=='nt'
def tool(name):
    ext=('.bat' if name in ('d8','apksigner') else '.exe') if windows else ''
    return str(bt/(name+ext))
def run(cmd):
    print('실행:', ' '.join(map(str,cmd)),flush=True);subprocess.run(list(map(str,cmd)),check=True)
java_bin=Path(os.environ['JAVA_HOME'])/'bin' if os.environ.get('JAVA_HOME') else None
def java(name):return str(java_bin/(name+('.exe' if windows else ''))) if java_bin else name
compiler=[java('javac')] if shutil.which(java('javac')) else [java('java'),'-m','jdk.compiler/com.sun.tools.javac.Main']
run([*compiler,'-source','8','-target','8','-encoding','UTF-8','-bootclasspath',str(bt/'core-lambda-stubs.jar')+os.pathsep+str(jar),'-classpath',jar,'-d',classes,*sorted((root/'src').rglob('*.java'))])
run([*compiler,'-source','8','-target','8','-encoding','UTF-8','-classpath',classes,'-d',classes,root/'tests/TrialTest.java'])
run([java('java'),'-cp',classes,'TrialTest'])
(classes/'TrialTest.class').unlink()
run([tool('d8'),'--lib',jar,'--min-api','30','--output',dex,*sorted(classes.rglob('*.class'))])
unsigned=build/'unsigned.apk';aligned=build/'aligned.apk';apk=build/'ZetaMesh-V3-dev.apk'
run([tool('aapt2'),'link','-I',jar,'--manifest',root/'AndroidManifest.xml','-o',unsigned])
with zipfile.ZipFile(unsigned,'a',zipfile.ZIP_DEFLATED) as z:
    for file in dex.glob('*.dex'): z.write(file,file.name)
run([tool('zipalign'),'-f','4',unsigned,aligned])
key=args.keystore.resolve();key.parent.mkdir(parents=True,exist_ok=True)
if not key.exists(): run([java('keytool'),'-genkeypair','-keystore',key,'-storepass','android','-keypass','android','-alias','androiddebugkey','-dname','CN=ZetaMesh Development','-keyalg','RSA','-keysize','2048','-validity','3650'])
run([tool('apksigner'),'sign','--ks',key,'--ks-key-alias','androiddebugkey','--ks-pass','pass:android','--key-pass','pass:android','--out',apk,aligned])
run([tool('apksigner'),'verify','--verbose',apk])
run([tool('aapt2'),'dump','badging',apk])
meta={'os':platform.platform(),'python':sys.version,'compile_sdk':35,'target_sdk':35,'min_sdk':30,'build_tools':'35.0.0','apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'physical_fold3_tested':False,'ttff_improvement_measured':False,'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [root/'AndroidManifest.xml',*sorted((root/'src').rglob('*.java'))]}}
(root/'verification/build.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print('APK:',apk)
