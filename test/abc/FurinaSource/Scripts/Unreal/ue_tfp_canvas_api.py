import unreal,json
R={'props':[x for x in dir(unreal.SystemLibrary) if 'property_by_name' in x],'canvas':unreal.RenderingLibrary.begin_draw_canvas_to_render_target.__doc__};json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\tfp_canvas_api.json','w'))
