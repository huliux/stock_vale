// 合并多个JSON文件并提取企业性质类型
import fs from 'fs';

// 要合并的文件列表
const files = ['page1.json', 'page2.json', 'page3.json', 'page4.json'];

// 存储所有企业性质类型
const actEntTypes = new Set();

// 处理每个文件
files.forEach(file => {
  try {
    if (fs.existsSync(file)) {
      const jsonData = fs.readFileSync(file, 'utf8');
      const data = JSON.parse(jsonData);

      if (data.results && Array.isArray(data.results)) {
        data.results.forEach(stock => {
          if (stock.act_ent_type) {
            actEntTypes.add(stock.act_ent_type);
          }
        });
      }
    }
  } catch (error) {
    console.error(`处理文件 ${file} 时出错:`, error);
  }
});

// 将结果按字母顺序排序并输出
const sortedTypes = Array.from(actEntTypes).sort();
console.log('找到的企业性质类型:');
sortedTypes.forEach(type => console.log(`- ${type}`));
console.log(`\n总共找到 ${sortedTypes.length} 种企业性质类型`);
