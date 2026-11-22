def lime_available():
    try:
        import lime
        return True
    except ImportError:
        return False
