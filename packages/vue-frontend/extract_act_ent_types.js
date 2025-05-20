// 提取企业性质类型的脚本
const fs = require('fs');

// 从命令行参数获取JSON文件路径
const jsonFilePath = process.argv[2];

if (!jsonFilePath) {
  console.error('请提供JSON文件路径作为参数');
  process.exit(1);
}

try {
  // 读取JSON文件
  const jsonData = fs.readFileSync(jsonFilePath, 'utf8');
  const data = JSON.parse(jsonData);
  
  // 提取所有企业性质类型
  const actEntTypes = new Set();
  
  if (data.results && Array.isArray(data.results)) {
    data.results.forEach(stock => {
      if (stock.act_ent_type) {
        actEntTypes.add(stock.act_ent_type);
      }
    });
  }
  
  // 将结果按字母顺序排序并输出
  const sortedTypes = Array.from(actEntTypes).sort();
  console.log('找到的企业性质类型:');
  sortedTypes.forEach(type => console.log(`- ${type}`));
  console.log(`\n总共找到 ${sortedTypes.length} 种企业性质类型`);
  
} catch (error) {
  console.error('处理JSON文件时出错:', error);
  process.exit(1);
}
