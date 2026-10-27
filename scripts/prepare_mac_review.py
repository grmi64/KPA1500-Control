"""Generate an isolated, stable-origin Mac review wrapper; never launch it."""
import argparse,ast,json,plistlib,uuid
from pathlib import Path

IDENTIFIER='com.grmi64.KPA1500Control.WindowsReview'
STORE_ID='d6b66ffd-180c-4f39-9b0e-547153c3d88b'

def replace_once(source,old,new):
    if source.count(old)!=1:raise ValueError('Mac wrapper changed; review harness anchors before generating.')
    return source.replace(old,new)

def render(source,settings,port,store_id=STORE_ID,identifier=IDENTIFIER):
    if type(port) is not int or not 1024<=port<=65535 or port==51980:
        raise ValueError('Choose a stable review-only port (1024..65535, excluding production 51980).')
    path=str(settings)
    if any(c in path for c in '\n\r\t\x00'):raise ValueError('Invalid settings path.')
    source=replace_once(source,'    var compact = false',f'    var compact = false\n    let reviewDefaults = UserDefaults(suiteName: "{identifier}")!')
    source=replace_once(source,'        let identifier = Bundle.main.bundleIdentifier ?? "com.grmi64.KPA1500Control"',f'''        let identifier = "{identifier}"
        guard Bundle.main.bundleIdentifier == identifier else {{
            showError("Review bundle identity mismatch; refusing startup.")
            NSApp.terminate(nil); return
        }}''')
    source=replace_once(source,'        window.setFrameAutosaveName("KPA1500MainWindow")','''        // Review geometry never uses Cocoa's implicit standard-domain autosave.
        if let stored = reviewDefaults.string(forKey: "ReviewMainFrame") {
            window.setFrame(NSRectFromString(stored), display: false)
        }''')
    source=replace_once(source,'        let config = WKWebViewConfiguration()',f'''        let config = WKWebViewConfiguration()
        if #available(macOS 14.0, *) {{
            config.websiteDataStore = WKWebsiteDataStore(forIdentifier: UUID(uuidString: "{store_id}")!)
        }} else {{
            showError("This isolated review harness requires macOS 14 or later.")
            NSApp.terminate(nil); return
        }}''')
    source=replace_once(source,'        var args = ["--no-browser","--http-port","51980"]\n        if CommandLine.arguments.contains("--demo") { args.append("--demo") }',
        '        let args = ['+', '.join(json.dumps(x,ensure_ascii=False) for x in ['--no-browser','--demo','--http-port',str(port),'--settings',path])+']')
    source=source.replace('UserDefaults.standard','reviewDefaults')
    source=replace_once(source,'        shuttingDown = true','''        shuttingDown = true
        if let window = window {
            reviewDefaults.set(NSStringFromRect(window.frame), forKey: "ReviewMainFrame")
            reviewDefaults.synchronize()
        }''')
    return source

def prepare(project,output,settings,port):
    project=Path(project).resolve();output=Path(output).resolve();settings=Path(settings).resolve()
    private=project/'.tmp'
    if not output.is_relative_to(private) or not settings.is_relative_to(private):
        raise ValueError('Generated wrapper and fresh settings must stay inside this checkout\'s .tmp folder.')
    if settings.exists():raise ValueError('Start with fresh review settings; do not copy production settings.')
    if output.exists():raise ValueError('Use a new output directory; existing review data is never overwritten.')
    store_id=str(uuid.uuid4());identifier=IDENTIFIER+'.'+uuid.uuid4().hex
    generated=render((project/'Sources/App.swift').read_text(encoding='utf-8'),settings,port,store_id,identifier)
    versions={}
    for node in ast.parse((project/'Sources/version.py').read_text(encoding='utf-8')).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('VERSION','BUILD'):
            versions[node.targets[0].id]=ast.literal_eval(node.value)
    output.mkdir(parents=True);settings.parent.mkdir(parents=True,exist_ok=True)
    (output/'App.swift').write_text(generated,encoding='utf-8')
    (output/'Info.plist').write_bytes(plistlib.dumps(dict(CFBundleIdentifier=identifier,CFBundleName='KPA1500 Windows Review',CFBundleDisplayName='KPA1500 Windows Review',CFBundleExecutable='KPA1500Control',CFBundlePackageType='APPL',CFBundleShortVersionString=versions['VERSION'],CFBundleVersion=versions['BUILD'],CFBundleIconFile='AppIcon.icns',LSMinimumSystemVersion='14.0',NSHighResolutionCapable=True,NSPrincipalClass='NSApplication')))
    (output/'review-plan.json').write_text(json.dumps(dict(bundle_identifier=identifier,web_data_store=store_id,http_port=port,settings=str(settings),offline_only=True,geometry_domain=identifier),indent=2),encoding='utf-8')
    return output

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--settings',type=Path,required=True)
    parser.add_argument('--port',type=int,default=51981);args=parser.parse_args()
    print(prepare(Path(__file__).resolve().parents[1],args.output,args.settings,args.port))

if __name__=='__main__':main()
