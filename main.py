import streamlit as st
import ftplib
import ftputil

# 1. 页面配置必须在最顶部
st.set_page_config(page_title="FTP 文件管理器", page_icon="📂")


# 2. 自定义类定义
class MySession(ftplib.FTP):
    def __init__(self, host_addr, username, password, port):
        ftplib.FTP.__init__(self)
        self.connect(host_addr, port)
        self.login(username, password)


# 3. 核心功能函数封装
def get_ftp_host(host_addr, port, username, password):
    """获取 FTP 连接实例"""
    try:
        # 使用 ftputil.FTPHost 时，建议在外部通过 with 语句使用以确保资源释放
        return ftputil.FTPHost(host_addr, username, password, port=port, session_factory=MySession)
    except Exception as e:
        st.error(f"连接失败: {e}")
        return None


def fetch_file_list(host_addr, port, username, password, remote_path):
    """获取远程目录下的文件列表并生成 Markdown 字符串"""
    host = get_ftp_host(host_addr, port, username, password)
    if not host:
        return None

    try:
        with host:  # 确保操作完成后关闭连接
            names = host.listdir(remote_path)
            file_list_md = ""
            for name in names:
                full_path = host.path.join(remote_path, name)
                is_file = host.path.isfile(full_path)
                icon = "📄" if is_file else "📁"
                file_list_md += f"{icon} {name}  \n"
            return file_list_md
    except Exception as e:
        st.error(f"读取目录失败: {e}")
        return None


# 4. 页面 UI 与交互逻辑
st.title("📂 FTP 文件传输助手")

# 侧边栏配置
with st.sidebar:
    st.header("连接设置")
    host_addr = st.text_input("主机地址", value="192.168.0.103")
    port = st.number_input("端口", value=6764, step=1)
    username = st.text_input("用户名", value="pc")
    password = st.text_input("密码", value="123456", type="password")
    remote_path = st.text_input("远程目录", value="/device/资料存储")
    connect_btn = st.button("刷新文件列表", type="primary", use_container_width=True)

# 初始化或刷新文件列表
if 'file_df' not in st.session_state or connect_btn:
    st.session_state.file_df = fetch_file_list(host_addr, port, username, password, remote_path)
    if connect_btn and st.session_state.file_df is not None:
        st.success("列表已更新")

# 显示文件列表
if st.session_state.file_df:
    with st.container():
        st.markdown(st.session_state.file_df)
elif st.session_state.file_df is None:
    st.warning("暂无文件数据，请检查连接设置或目录路径。")

st.divider()  # 添加一条分割线，区分列表和上传区域

# 文件上传区
uploaded_file = st.file_uploader("点击或拖拽上传文件", label_visibility="visible")
upload_btn = st.button("上传文件", type="primary")

if upload_btn:
    if uploaded_file is not None:
        host = get_ftp_host(host_addr, port, username, password)
        if host:
            try:
                with host:
                    remote_file_path = host.path.join(remote_path, uploaded_file.name)
                    with host.open(remote_file_path, 'wb') as remote_file:
                        remote_file.write(uploaded_file.getvalue())
                st.success(f"文件 `{uploaded_file.name}` 上传成功！")
                # 可选：上传成功后自动刷新列表
                st.session_state.file_df = fetch_file_list(host_addr, port, username, password, remote_path)
            except Exception as e:
                st.error(f"上传失败: {e}")
    else:
        st.warning("请先选择一个要上传的文件。")