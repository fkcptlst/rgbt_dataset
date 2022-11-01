import re
# test_str = '<box frame="1" xtl="154" ytl="298" xbr="168" ybr="326" outside="0" occluded="0"><attribute id="1345">not_keep_out</attribute><attribute id="1347">not_shake</attribute><attribute id="1348">street</attribute><attribute id="1341">30m</attribute><attribute id="1343">bright_light</attribute></box>'
altitude_pattern_re = re.compile(r'<attribute id="[0-9]+">(?P<value>[0-9]+m)')
cam_mov_pattern_re = re.compile(r'<attribute id="[0-9]+">(?P<value>shake|not_shake)')

def change_altitude_id(matched):
    value = matched.group('value')
    return '<attribute id="1">' + value

def change_cam_mov_id(matched):
    value = matched.group('value')
    return '<attribute id="2">' + value

# read from test.xml
with open('test.xml', 'r') as f:
    # replace altitude_id
    for line in f:
        line = altitude_pattern_re.sub(change_altitude_id, line)
        print(line)
    # write to test_new.xml
    # f.write(new_str)