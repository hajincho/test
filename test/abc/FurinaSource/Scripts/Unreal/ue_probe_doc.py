import unreal
open(r"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\ue_probe_doc.txt", 'w').write(
    unreal.IKRetargetBatchOperation.duplicate_and_retarget.__doc__ + '\n----\n' + unreal.IKRetargetBatchOperation.run_batch_retarget.__doc__)
