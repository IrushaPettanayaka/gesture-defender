"""Gesture Defender command-line entry point."""
import argparse
import os
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')


def main():
    from startup import configure, report_failure
    log_path = configure()
    parser = argparse.ArgumentParser(description='Gesture Defender: local webcam arcade game')
    parser.add_argument('--camera', type=int, default=None, help='select camera and start webcam mode')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--keyboard', '--demo', dest='keyboard', action='store_true', default=None,
                       help='keyboard-only mode (default); no camera access')
    modes.add_argument('--webcam', dest='keyboard', action='store_false', help='start webcam mode')
    parser.add_argument('--smoke-frames', type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument('--diagnostics', metavar='JSON_PATH', help='check bundled models and write metadata only')
    parser.add_argument('--check-camera', action='store_true', help='also open the camera during diagnostics')
    parser.add_argument('--verify-controls', metavar='JSON_PATH', help='30-second real webcam gesture check (metadata only)')
    parser.add_argument('--verify-ui', metavar='OUTPUT_DIR', help='exercise UI with synthetic camera data; save review images and a report')
    args = parser.parse_args()
    try:
        if args.verify_ui:
            from ui_check import verify
            return verify(args.verify_ui)
        if args.verify_controls:
            from live_check import verify
            return verify(args.verify_controls, camera_index=args.camera or 0)
        if args.diagnostics:
            from diagnostics import run_checks
            return run_checks(args.diagnostics, args.check_camera)
        keyboard = args.keyboard if args.keyboard is not None else args.camera is None
        from app import run
        return run(args.camera, keyboard, args.smoke_frames)
    except Exception:
        report_failure(log_path)
        return 1
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
