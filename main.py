from rag_modules import insert, clear, refer


def main():
    print("Hello from rag!")
    docs = [
        "Newton's laws of motion form the foundation of classical mechanics.",
        "The periodic table organizes elements by their atomic number and properties.",
        "DNA carries genetic information in all living organisms.",
        "Photosynthesis converts sunlight into chemical energy in plants.",
        "Einstein's theory of relativity revolutionized our understanding of space and time.",
        "The mitochondria is known as the powerhouse of the cell.",
        "Quantum mechanics describes the behavior of matter at the atomic scale.",
        "The speed of light in vacuum is approximately 299,792,458 meters per second.",
        "Chemical bonds form when atoms share or transfer electrons.",
        "The human brain contains approximately 86 billion neurons.",
        "Thermodynamics governs energy transfer and transformation in physical systems.",
        "Evolution by natural selection explains the diversity of life on Earth.",
        "The electromagnetic spectrum includes radio waves, microwaves, and visible light.",
        "Protein synthesis occurs through transcription and translation processes.",
        "Mathematical calculus is essential for understanding rates of change.",
        "The structure of an atom consists of protons, neutrons, and electrons.",
        "Mendel's laws describe the inheritance patterns of genetic traits.",
        "The carbon cycle is crucial for maintaining Earth's climate balance.",
        "Semiconductor materials are fundamental to modern electronic devices.",
        "Antibiotics work by targeting specific bacterial cellular processes."
    ]
    # 示例数据


    clear.clear_data()  # 清除数据
    insert.insert_data(docs)  # 插入数据
    queries = ["What's DNA?", "What is the speed of light?"]
    results = []
    for query in queries:
        results.append(refer.get_reference(query))
    
    print("Search Results:")
    for i, result_group in enumerate(results):
        print(f"Query {i+1} results:")
        for result in result_group:
            print(f"  - {result}")
            
if __name__ == "__main__":
    main()
