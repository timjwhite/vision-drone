def main():
    config = load_config()

    camera_manager = CameraManager(config.cameras)
    vision_engine  = VisionEngine(config.vision)
    fusion_engine  = FeatureFusion(config.fusion)
    music_engine   = MusicEngine(config.music)
    midi_engine    = MidiOutput(config.midi)
    visual_engine  = VisualEngine(config.visuals)

    camera_manager.start()

    while True:
        frames = camera_manager.get_latest_frames()

        vision_results = vision_engine.process(frames)
        global_features = fusion_engine.update(vision_results)

        midi_events = music_engine.generate(global_features)
        midi_engine.send(midi_events)

        visual_engine.render(frames, vision_results, global_features)

        sleep(config.tick_interval)
