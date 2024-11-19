import autogen
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from typing_extensions import Annotated
from langchain.prompts import PromptTemplate
import os
import re
import sqlite3

# openai api key
api_key = ""

os.environ["OPENAI_API_KEY"] = api_key

# load env variables
load_dotenv()

# query_maker_gpt_system_prompt = '''You are SQL Query Generator. Kindly generate the sql query only and use only the listed columns in
# below schema. Use only the columns available in the Schema below.
#
# Below is the Schema of the available tables to make the sql queries. Create and return only one query.
#
# CREATE TABLE IF NOT EXISTS dishes (
# id INTEGER PRIMARY KEY AUTOINCREMENT,
# name TEXT NOT NULL UNIQUE,
# quantity INTEGER NOT NULL
#
#
# only use the above mentioned columns in making sql query.
# User Input:
# '''
#
# admin_prompt = "Admin"
# assistant_agent_prompt = '''
# Do not change user input. You have the opportunity to advise the Admin on selecting the appropriate function, along with the required arguments. The "query_maker" function is designed to accept human input as an argument and construct the SQL query. Meanwhile, the "run_sql_query" function is responsible for executing the query. Please refrain from independently crafting SQL queries.
# Once you receive the results from the Admin in response to the SQL query, ensure that you interpret them accurately. You are also authorized to create SQL queries tailored to user input. Subsequently, execute the query and provide the results. In the event of any errors, please rectify them and rerun the query, and then present the answer.
# If the query result is empty, then just say we do not have this data in database.
# '''


query_maker_gpt_system_prompt = '''
Bạn là một Trình Tạo Truy Vấn SQL. Vui lòng tạo câu lệnh SQL `UPDATE` chỉ và sử dụng chỉ các cột được liệt kê trong 
schema dưới đây. Chỉ sử dụng các cột có trong Schema dưới đây.

Dưới đây là Schema của các bảng có sẵn để tạo các truy vấn SQL. Tạo và trả về chỉ duy nhất một truy vấn .

CREATE TABLE IF NOT EXISTS dishes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    quantity INTEGER NOT NULL
);

Chỉ sử dụng các cột đã đề cập ở trên để tạo câu lệnh SQL `UPDATE` nhằm giảm số lượng sản phẩm khi đặt hàng.
Cụ thể, hãy đảm bảo rằng câu lệnh `UPDATE` luôn giảm giá trị của cột `quantity` dựa trên số lượng được yêu cầu.
User Input: 
'''

admin_prompt = "Admin"

assistant_agent_prompt = '''
Không thay đổi đầu vào của người dùng. Bạn có cơ hội tư vấn cho Admin về việc chọn chức năng phù hợp, cùng với các tham số cần thiết. Hàm "query_maker" được thiết kế để nhận đầu vào từ người dùng và xây dựng câu lệnh SQL. Trong khi đó, hàm "run_sql_query" chịu trách nhiệm thực thi câu lệnh SQL. Vui lòng không tự tạo câu lệnh SQL một cách độc lập.

Sau khi bạn nhận được kết quả từ Admin liên quan đến câu lệnh SQL, hãy đảm bảo rằng bạn diễn giải chúng một cách chính xác. Bạn cũng được ủy quyền để tạo các câu lệnh SQL phù hợp với đầu vào của người dùng. Sau đó, thực thi câu lệnh và cung cấp kết quả. Trong trường hợp có bất kỳ lỗi nào, vui lòng sửa chữa và chạy lại câu lệnh, sau đó trình bày câu trả lời.

Nếu kết quả truy vấn trống, thì chỉ cần nói rằng chúng tôi không có dữ liệu này trong cơ sở dữ liệu.
'''

# Set your LLms Endpoint
config_list_gpt_turbo = autogen.config_list_from_models(model_list=["gpt-4o-mini-2024-07-18"])


def query_maker(user_input):
    # make sql queries using LLM chain
    openaiLLM = ChatOpenAI(model="gpt-4o-mini-2024-07-18", temperature=0, openai_api_key=api_key, cache=False)
    prompt_template = PromptTemplate.from_template("{system_prompt} + '\n' +  {user_input}.")

    chain = prompt_template | openaiLLM
    query1 = chain.invoke({"system_prompt": query_maker_gpt_system_prompt, "user_input": user_input})
    query2 = chain.invoke({"system_prompt": query_maker_gpt_system_prompt, "user_input": user_input})

    return query1, query2


def run_sql_query(sql_query):
    db_name = "dishes.db"

    try:
        connection = sqlite3.connect(db_name)
        cursor = connection.cursor()

        print(sql_query)

        pattern = r"UPDATE\s+dishes\s+SET\s+quantity\s*=\s*quantity\s*-\s*(\d+)\s+WHERE\s+name\s*=\s*'(.+?)';?"
        match = re.search(pattern, sql_query, re.IGNORECASE)

        if not match:
            cursor.close()
            connection.close()
            return "Câu lệnh SQL không hợp lệ."

        quantity_to_decrement = int(match.group(1))
        dish_name = match.group(2)

        select_query = "SELECT quantity FROM dishes WHERE name = ?;"
        cursor.execute(select_query, (dish_name,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            connection.close()
            return "Món ăn này chúng tôi không có sẵn."

        current_quantity = result[0]

        if current_quantity < quantity_to_decrement:
            cursor.close()
            connection.close()
            return f"Số lượng sản phẩm {dish_name} chỉ còn {current_quantity} trong db."

        cursor.execute(sql_query)
        connection.commit()

        if cursor.rowcount > 0:
            result_status = "THÀNH CÔNG ĐẶT HÀNG"
        else:
            result_status = "THẤT BẠI"

        cursor.close()
        connection.close()

        return result_status

    except sqlite3.Error as e:
        print("Lỗi khi kết nối tới cơ sở dữ liệu SQLite:", e)
        return "THẤT BẠI"

# def compare_multiple_query_maker(script: Annotated[str, "Valid Python cell to execute."]):
#     return user_proxy.execute_code_blocks([('python', script)])


# another way of registering functions is to use the register_function
def draw_graph(script: Annotated[str, "Valid Python cell to execute."]) -> str:
    return user_proxy.execute_code_blocks([('python', script)])


gpt_turbo_config = {
    "temperature": 0,
    "config_list": config_list_gpt_turbo,
    "functions": [
        {
            "name": "query_maker",
            "description": "generates sql query as per user input",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": "This is the input from the user side.",
                    }
                    ,
                },
                "required": ["user_input"],
            },
        },

        # {
        #     "name": "compare_sql_queries",
        #     "description": "generate python code that compares 2 queries. If the 2 queries are the same, return 1 of the 2 queries. Otherwise, if the 2 queries are different, run the query_maker function again. You can only run it a maximum of 5 times.",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "user_input": {
        #                 "type": "string",
        #                 "description": "This is input from query_maker function",
        #             }
        #             ,
        #         },
        #         "required": ["script"],
        #     },
        # },

        {
            "name": "run_sql_query",
            "description": "This function is used to run sql query against user input to get the results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "This is the mysql query.",
                    }
                    ,
                },
                "required": ["sql_query"],
            },
        },
    ]
}
function_map = {"query_maker": query_maker,
                # "compare_sql_queries": compare_multiple_query_maker,
                "run_sql_query": run_sql_query}

# termination_msg = ("If everything looks good, respond with Approved"
#                    " or If the result cannot be returned then respond with Approved")

termination_msg = (
    "If everything looks good, respond with 'Approved'. "
    "If the result cannot be returned, respond with 'Rejected'."
)

def is_termination_msg(content):
    have_content = content.get("content", None) is not None
    if have_content:
        return True
    else:
        return False


user_proxy = autogen.UserProxyAgent(
    name="Admin",
    system_message=admin_prompt + termination_msg,
    human_input_mode="NEVER",
    is_termination_msg=is_termination_msg,
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False
    }

)

engineer = autogen.AssistantAgent(
    name="Assistant Agent",
    llm_config=gpt_turbo_config,
    system_message=assistant_agent_prompt + termination_msg,
    function_map=function_map,
)


user_input = 'tôi muốn đặt 1  '

user_proxy.register_function(function_map={"query_maker": query_maker,
                                           # "compare_sql_queries": compare_multiple_query_maker,
                                           "run_sql_query": run_sql_query})

user_proxy.initiate_chat(engineer, message=f"{user_input}", clear_history=True)

user_proxy_chat = user_proxy.chat_messages
engineer_chat = engineer.chat_messages
