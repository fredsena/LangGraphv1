"""
Simple test to verify virtual filesystem debugging works
"""
import asyncio
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from utils.state import DeepAgentState
from utils.file_tools import ls, read_file, write_file
from utils.prompts import FILE_USAGE_INSTRUCTIONS


async def main():
    llm = ChatOpenAI(
        model="qwen/qwen3-4b-2507", 
        base_url="http://127.0.0.1:1234/v1", 
        temperature=0.0, 
        api_key="11111111111111"
    )

    tools = [ls, read_file, write_file]

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=FILE_USAGE_INSTRUCTIONS,
        state_schema=DeepAgentState,
    )

    print("\n" + "=" * 80)
    print("Starting agent with empty filesystem...")
    print("=" * 80 + "\n")

    result = await agent.ainvoke(
        {
            "messages": [{
                "role": "user",
                "content": "Create a file called 'test.txt' with the content 'Hello World'. Then list all files.",
            }],            
            "files": {},
        }
    )

    # ==================== DEBUG SECTION ====================
    print("\n" + "🔍 " * 20)
    print("VIRTUAL FILESYSTEM DEBUG")
    print("🔍 " * 20 + "\n")

    files_count = len(result["files"])
    print(f"Total files created: {files_count}\n")

    if files_count > 0:
        for filename, content in result["files"].items():
            line_count = len(content.splitlines())
            char_count = len(content)
            
            print(f"{'=' * 60}")
            print(f"📄 FILE: {filename}")
            print(f"{'=' * 60}")
            print(f"📊 Stats: {line_count} lines, {char_count} characters")
            print(f"{'-' * 60}")
            print(content)
            print(f"{'-' * 60}\n")
    else:
        print("⚠️  No files were created in the virtual filesystem")
        
    print("🔍 " * 20 + "\n")
    # ==================== END DEBUG SECTION ====================

    # ==================== SAVE TO DISK ====================
    from pathlib import Path
    
    if result["files"]:
        save_dir = Path("./virtual_files")
        save_dir.mkdir(exist_ok=True)
        
        print("\n" + "💾 " * 20)
        print("SAVING VIRTUAL FILES TO DISK")
        print("💾 " * 20 + "\n")
        
        for filename, content in result["files"].items():
            # Sanitize filename for actual filesystem
            safe_filename = filename.replace("/", "_").replace("\\", "_")
            filepath = save_dir / safe_filename
            filepath.write_text(content)
            print(f"✅ Saved: {filepath.absolute()}")
        
        print(f"\n📁 All files saved to: {save_dir.absolute()}")
        print("💾 " * 20 + "\n")
    # ==================== END SAVE TO DISK ====================

    print("\n" + "=" * 80)
    print("Agent Messages:")
    print("=" * 80 + "\n")
    
    for msg in result["messages"][-3:]:  # Show last 3 messages
        msg.pretty_print()


if __name__ == "__main__":
    asyncio.run(main())
