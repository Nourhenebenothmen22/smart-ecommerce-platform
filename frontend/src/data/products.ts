export type Product = {
  id: string;
  name: string;
  price: number;
  category: string;
  subcategory: string;
  slug?: string;
  nameKey: string;
  image: string;
  descriptionKey: string;
  description: string;
};

export type CategoryGroup = {
  name: string;
  subcategories: string[];
};

export const categories: CategoryGroup[] = [
  {
    name: 'Electronics',
    subcategories: ['Phones', 'Laptops', 'Headphones'],
  },
  {
    name: 'Fashion',
    subcategories: ['Men', 'Women', 'Shoes'],
  },
  {
    name: 'Home',
    subcategories: ['Decor', 'Furniture', 'Kitchen'],
  },
];

export const products: Product[] = [
  {
    id: '1',
    name: 'Atlas Pro Smartphone',
    nameKey: 'catalog.products.1.name',
    price: 699,
    category: 'Electronics',
    subcategory: 'Phones',
    image: '/hero/hero1.png',
    descriptionKey: 'catalog.products.1.description',
    description: 'A polished smartphone with a vivid display, fast performance, and reliable all-day battery life.',
  },
  {
    id: '2',
    name: 'Nomad Ultra Laptop',
    nameKey: 'catalog.products.2.name',
    price: 1199,
    category: 'Electronics',
    subcategory: 'Laptops',
    image: '/hero/hero2.png',
    descriptionKey: 'catalog.products.2.description',
    description: 'A lightweight laptop designed for productivity, creative work, and smooth multitasking.',
  },
  {
    id: '3',
    name: 'Sahara Wireless Headphones',
    nameKey: 'catalog.products.3.name',
    price: 149,
    category: 'Electronics',
    subcategory: 'Headphones',
    image: '/hero/hero3.png',
    descriptionKey: 'catalog.products.3.description',
    description: 'Comfortable wireless headphones with rich sound, deep bass, and long battery life.',
  },
  {
    id: '4',
    name: 'Medina Linen Jacket',
    nameKey: 'catalog.products.4.name',
    price: 89,
    category: 'Fashion',
    subcategory: 'Men',
    image: '/hero/hero1.png',
    descriptionKey: 'catalog.products.4.description',
    description: 'A breathable linen jacket with a refined cut for smart casual everyday styling.',
  },
  {
    id: '5',
    name: 'Amani Flow Dress',
    nameKey: 'catalog.products.5.name',
    price: 115,
    category: 'Fashion',
    subcategory: 'Women',
    image: '/hero/hero2.png',
    descriptionKey: 'catalog.products.5.description',
    description: 'An elegant dress with soft movement, premium fabric, and a graceful modern silhouette.',
  },
  {
    id: '6',
    name: 'Oasis Leather Sneakers',
    nameKey: 'catalog.products.6.name',
    price: 132,
    category: 'Fashion',
    subcategory: 'Shoes',
    image: '/hero/hero3.png',
    descriptionKey: 'catalog.products.6.description',
    description: 'Premium everyday sneakers with a clean profile, cushioned sole, and durable leather finish.',
  },
  {
    id: '7',
    name: 'Zellige Wall Decor Set',
    nameKey: 'catalog.products.7.name',
    price: 74,
    category: 'Home',
    subcategory: 'Decor',
    image: '/hero/hero1.png',
    descriptionKey: 'catalog.products.7.description',
    description: 'A decorative set inspired by geometric craftwork, made to bring warmth to living spaces.',
  },
  {
    id: '8',
    name: 'Casbah Lounge Chair',
    nameKey: 'catalog.products.8.name',
    price: 349,
    category: 'Home',
    subcategory: 'Furniture',
    image: '/hero/hero2.png',
    descriptionKey: 'catalog.products.8.description',
    description: 'A comfortable accent chair with premium upholstery and a sculptural, lounge-ready profile.',
  },
  {
    id: '9',
    name: 'Amber Kitchen Essentials',
    nameKey: 'catalog.products.9.name',
    price: 58,
    category: 'Home',
    subcategory: 'Kitchen',
    image: '/hero/hero3.png',
    descriptionKey: 'catalog.products.9.description',
    description: 'A refined kitchen set for daily cooking, serving, and organized countertop storage.',
  },
];
