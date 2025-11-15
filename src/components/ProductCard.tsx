import React from 'react';

interface ProductCardProps {
  productName: string;
  productLink: string;
  imageUrl: string;
  description: string;
  manipulativeTactics: string[];
  userQuestion: string;
}

const ProductCard: React.FC<ProductCardProps> = ({
  productName,
  productLink,
  imageUrl,
  description,
  manipulativeTactics,
  userQuestion,
}) => {
  return (
    <div className="p-4 border border-red-300 rounded-lg shadow-lg bg-red-50 max-w-sm mx-auto my-4">
      <h2 className="text-xl font-bold text-red-800 mb-2">{productName}</h2>
      <a
        href={productLink}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 hover:text-blue-800 underline block mb-3"
      >
        View Product Page
      </a>
      <div className="mb-3">
        <img
          src={imageUrl}
          alt={`Image of ${productName}`}
          className="w-full h-40 object-cover rounded-md border border-red-200"
        />
      </div>
      <p className="text-sm text-gray-700 mb-4">{description}</p>

      <div className="mt-4 p-3 bg-white border border-red-200 rounded-md">
        <h3 className="text-lg font-semibold text-red-700 mb-2">
          Marketing Tactic Analysis
        </h3>
        <p className="text-sm text-gray-600 mb-2">
          This product appears to use the following potentially manipulative marketing tactics:
        </p>
        <ul className="list-disc list-inside text-sm text-red-600 space-y-1">
          {manipulativeTactics.map((tactic, index) => (
            <li key={index} className="font-medium">
              {tactic}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-4 p-3 bg-red-100 border-l-4 border-red-500 rounded-r-md">
        <p className="font-bold text-red-800">{userQuestion}</p>
      </div>
    </div>
  );
};

export default ProductCard;
