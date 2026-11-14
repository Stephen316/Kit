def unsplit_tag(tag_id, reversed_direction):
    if not isinstance(tag_id, int) or not 0 < tag_id < 1 << 64:
        raise ValueError('A positive authored sketch tag is required')
    if not isinstance(reversed_direction, bool):
        raise ValueError('Direction must be an explicit boolean')
    return dict(version=3, tagId=tag_id, secondaryTagId=0, direction=int(reversed_direction), splitSequenceId=1, splitTotalNumber=1, objectOffset20=0)


def curve_recipe(tag_id, reversed_direction):
    return dict(version=0, sketchTags=[unsplit_tag(tag_id, reversed_direction)], objectOffset20Set=[], objectOffset38Set=[])


def circle_loop(tag_id):
    return {'first': [unsplit_tag(tag_id, False)], 'second': True}
