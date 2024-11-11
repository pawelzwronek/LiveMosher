def replace(target, replacement, file_path):
    with open(file_path, 'r', encoding='utf-8') as file_s:
        src = file_s.read()
        with open(target, 'r', encoding='utf-8') as file_t:
            dst = file_t.read()
        with open(target, 'w', encoding='utf-8') as file_t:
            file_t.write(dst.replace(replacement, src))

replace('src/script.py', '{EXAMPLE1}', 'Examples/basic.js')
replace('src/LiveMosherApp.py', '{APP_VERSION}', 'version.txt')
