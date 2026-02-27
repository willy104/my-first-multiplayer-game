import pygame
import json
import os






def creat_map(map_data,map_json_path=None):
    mapSurf=pygame.surface.Surface((1024,704),pygame.SRCALPHA)

    t_size=map_data["tilewidth"]
    map_w=map_data["width"]
    map_h=map_data["height"]

    tilesets={}

    for ts in map_data["tilesets"]:
        if "image" not in ts:
            print("ts missing",ts)
            continue
        img_path=ts["image"]
        if map_json_path:
            base_dir=os.path.dirname(os.path.abspath(map_json_path))
            img_path=os.path.join(base_dir,img_path)
            img_path=os.path.normpath(img_path)
        try:

            image=pygame.image.load(img_path).convert_alpha()
        except Exception as e:
            print(f"failed",e)
            continue
        tilesets[ts["firstgid"]]={
            "image":image,
            "columns":ts["columns"],
            "tilecount":ts["tilecount"],
            "margin":ts.get("margin",0),
            "spacing":ts.get("spacing",0),
            "t_w":ts["tilewidth"],
            "t_h":ts["tileheight"]
        }

    ground_layer=next(l for l in map_data["layers"] if l["name"]=="ground")
    ground_data=ground_layer["data"]


    for y in range(map_h):
        for x in range(map_w):
            tile_id=ground_data[y*map_w+x]
            if tile_id==0:
                continue
        
            ts=max(k for k in tilesets if k <=tile_id)
            tile_index=tile_id-ts
            ts_data=tilesets[ts]
            col=tile_index % ts_data["columns"]
            row=tile_index // ts_data["columns"]
            t_w=ts_data["t_w"]
            t_h=ts_data["t_h"]
            spacing=ts_data["spacing"]
            margin=ts_data["margin"]

            src_x=margin+col*(t_w+spacing)
            src_y=margin+row*(t_h+spacing)
            rect=pygame.Rect(src_x,src_y,t_w,t_h)
            mapSurf.blit(ts_data["image"],(x*t_size,y*t_size),rect)

        
    return mapSurf