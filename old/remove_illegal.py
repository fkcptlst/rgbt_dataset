import os
input_dir= '../annotation'

filenames = os.listdir(input_dir)
for filename in filenames:
    path = input_dir + '/' + filename
    with open(path, mode='r', errors='ignore') as f:
        lines = f.readlines()
        f.close()
    with open(path, mode='w', errors='ignore') as f:
        for line in lines:
            f.write(line)
        f.close()
