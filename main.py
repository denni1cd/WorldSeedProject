Admin_path = "Admin/AdminSetup.py"
with open(Admin_path) as f:
    code = compile(f.read(), Admin_path, 'exec')
    exec(code, globals())


Location_Generator_path = "Generators/Location_Generator.py"
with open(Location_Generator_path) as f:
    code = compile(f.read(), Location_Generator_path, 'exec')
    exec(code, globals())
