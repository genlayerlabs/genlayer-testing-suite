def safe_filename(filename: str) -> str:
    """
    Replace problematic characters in filename.
    """
    return (
        filename.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("-", "_")
        .replace(" ", "_")
        .replace(".py", "")
    )
