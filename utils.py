import os


def get_filename(path: str):
    """
    './data\\FM docs 2024.3\\JOM_1998_13_4_06_The_Application_of_the_Hardin_Jones-Pauling-.pdf'
    ->
    ('./data\\FM docs 2024.3',
    'JOM_1998_13_4_06_The_Application_of_the_Hardin_Jones-Pauling-.pdf')
    """
    basepath, filename = os.path.split(path)
    return filename


def format_references(references: list[str]) -> str:
    if len(references) == 0:
        return "\nno references."
    else:
        references = [f"*{reference}*" for reference in references]
        references_str = ", ".join(references)
        return f"\nreferences: \n{references_str}"


def download_dataset(
    dataset_repo='NagatoYuki0943/FMdocs',
    target_path='./data/'
):
    import os
    import openxlab
    from openxlab.dataset import get

    print("start download dataset")
    print(os.environ.keys())
    access_key = os.getenv("OPENXLAB_AK", "")
    secret_key = os.getenv("OPENXLAB_SK", "")
    print(f"access_key = {access_key}")
    print(f"secret_key = {secret_key}")
    openxlab.login(ak=access_key, sk=secret_key)
    get(dataset_repo=dataset_repo, target_path=target_path) # 数据集下载
    print("finish download dataset")


if __name__ == "__main__":
    download_dataset()