import os


def update_nested_dict(original, updates):
    """
    递归更新嵌套字典，存在的 key 替换，不存在的保留。
    :param original: 原始字典（会被修改）
    :param updates: 要更新的内容（新字典）
    :return: 更新后的原始字典
    """
    for key, value in updates.items():
        if isinstance(value, dict) and key in original and isinstance(original[key], dict):
            # 如果原字典中有该 key 且都是 dict，递归处理
            update_nested_dict(original[key], value)
        else:
            # 否则直接覆盖或新增
            original[key] = value
    return original


class EnhanceDict(dict):
    def __init__(self, data=None):
        # 初始化时将输入数据转换为 ConfigDict 类型
        super().__init__(data or {})

    def __getattr__(self, name):
        """
        通过属性访问键值。
        """
        value = self.get(name)
        if value is None:
            return NoneEnhance()
        if isinstance(value, dict):
            return EnhanceDict(value)
        return value

    def __setattr__(self, name, value):
        """
        通过属性设置键值。
        """
        self[name] = value

    def __getitem__(self, key):
        """
        重写 __getitem__ 方法，支持嵌套字典返回 ConfigDict。
        """
        value = super().__getitem__(key)
        if isinstance(value, dict):
            return EnhanceDict(value)
        return value

    def __setitem__(self, key, value):
        """
        重写 __setitem__ 方法，自动将字典类型的值转换为 ConfigDict。
        """
        if isinstance(value, dict):
            value = EnhanceDict(value)
        super().__setitem__(key, value)

    def update_from(self, other):
        self.update(update_nested_dict(dict(self), dict(other)))

    def get(self, key, default=None):
        """
        重写 get 方法，支持嵌套字典返回 ConfigDict。
        """
        value = super().get(key, default)
        if isinstance(value, dict):
            return EnhanceDict(value)
        return value


class NoneEnhance:
    def __getattr__(self, name):
        return NoneEnhance()

    def __bool__(self):
        return False


def value_or_default(value, default=None):
    if isinstance(value, NoneEnhance):
        return default
    return value


def read_prefixed_env_vars(prefix):
    """
    读取以指定前缀开头的环境变量，并将其转换为小写、嵌套的字典。

    :param prefix: 环境变量前缀（例如 "APP_"）
    :return: 转换后的嵌套字典
    """
    # 确保前缀是大写的，避免大小写问题
    prefix = prefix.upper()
    result = {}

    for key, value in os.environ.items():
        if key.startswith(prefix):
            # 去掉前缀部分并转为小写
            stripped_key = key[len(prefix):].lower()
            # 使用双下划线分割各个部分
            parts = stripped_key.split('__')

            current_level = result
            for part in parts[:-1]:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]

            # 尝试将字符串值解析为Python数据类型
            try:
                namespace = {}
                exec(f'data={value}', namespace)
                data = namespace['data']
            except:
                data = value  # 如果解析失败则保留原始字符串

            # 设置最终值
            current_level[parts[-1]] = data

            # 如果parts长度为1，则直接设置在result上
            if len(parts) == 1:
                result[stripped_key] = data

    return result


if __name__ == '__main__':
    import os

    data = EnhanceDict({"a": {"b": 1,"d":23},"f":3})
    print(data)
    data.update_from({"a": {"b": 2,"d":32323},"e":12})
    print(data)
