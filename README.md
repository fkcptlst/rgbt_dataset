[//]: # (- show_gt: 可视化)

[//]: # (- countMDMT: 统计)

[//]: # (- get_first_frame: 统计第一帧)

[//]: # (- make_csv: 制表)

## 解析数据

原始标注格式：

```xml

<annotations count="19">
    <track id="0" label="person">
        <box frame="0" xtl="137" ytl="26" xbr="153" ybr="65" outside="0" occluded="0">
            <attribute id="65">30m</attribute>
            <attribute id="67">bright_light</attribute>
            <attribute id="69">not_keep_out</attribute>
            <attribute id="71">not_shake</attribute>
            <attribute id="73">stadium</attribute>
        </box>
    </track>
</annotations>
```

```python
xml_dict = {
    "annotations_count": 19,
    "tracks_list": [
        {  # track_dict
            "id": 0,
            "label": "person",
            "box_list": [
                # box_dict
                {
                    "frame": 0,
                    "xtl": 137,
                    "ytl": 26,
                    "xbr": 153,
                    "ybr": 65,
                    "outside": 0,
                    "occluded": 0,
                    "attributes_list": [
                        {
                            "id": 65,
                            "value": "30m"
                        },
                        {
                            "id": 67,
                            "value": "bright_light"
                        },
                        {
                            "id": 69,
                            "value": "not_keep_out"
                        },
                        {
                            "id": 71,
                            "value": "not_shake"
                        },
                        {
                            "id": 73,
                            "value": "stadium"
                        }
                    ]  # attributes_list
                }  # box_dict
            ]  # box_list
        },  # track_dict
        {...}  # track_dict
    ]  # tracks_list
}
```

## 统计数据集
### scalar

#### sequence level

-[x] number of sequences
-[x] average number of frames per sequence
-[x] average tracks per sequence

#### category level
-[ ] number of categories
-[ ] distribution of categories

#### scene level
-[ ] number of scenes
-[ ] distribution of scenes


