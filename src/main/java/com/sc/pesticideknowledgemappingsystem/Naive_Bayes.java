//package com.sc.pesticideknowledgemappingsystem;
//
//import java.io.*;
//import java.util.*;
//
//import com.sc.pesticideknowledgemappingsystem.service.AnswerService;
//import org.apache.poi.ss.usermodel.*;
//import org.apache.spark.SparkConf;
//import org.apache.spark.api.java.JavaRDD;
//import org.apache.spark.api.java.JavaSparkContext;
//import org.apache.spark.mllib.classification.NaiveBayes;
//import org.apache.spark.mllib.classification.NaiveBayesModel;
//import org.apache.spark.mllib.linalg.Vector;
//import org.apache.spark.mllib.linalg.Vectors;
//import org.apache.spark.mllib.regression.LabeledPoint;
//
//import com.hankcs.hanlp.HanLP;
//import com.hankcs.hanlp.seg.Segment;
//import com.hankcs.hanlp.seg.common.Term;
//
///**
// * Spark贝叶斯分类器 + HanLP分词器 + 实现问题语句的抽象+模板匹配+关键性语句还原
// * @auhtor Appleyk
// * @blob   http://blog.csdn.net/appleyk
// * @date   updated on 2020年4月5日-下午21:00:00
// */
//public class Naive_Bayes {
//
//    /**指定问题question及字典的txt模板所在的根目录*/
//    private String rootDirPath;
//
//    /**Spark贝叶斯分类器*/
//    private NaiveBayesModel nbModel;
//
//    /**词语和下标的对应表   == 词汇表*/
//    private Map<String, Integer> vocabulary;
//
//    /** 分类模板索引*/
//    int modelIndex = 0;
//
//    public Naive_Bayes(String rootDirPath) throws Exception{
//        // 加载词汇表
//        vocabulary = loadVocabulary();
//        // 加载分类模型，初始化贝叶斯分类器对象
//        nbModel = loadClassifierModel();
//    }
//
//    /**
//     * 问句拆解，套用模板，得到关键word，核心方法实现
//     * @param abstractStr 问句
//     * @return 结果集合（问题模板索引、关键word数组）
//     * @throws Exception
//     */
//    public double analysis(String abstractStr) throws Exception {
//
//        /**将抽象的句子与Spark训练集中的模板进行匹配，拿到句子对应的模板*/
//        double index = queryClassify(abstractStr);
//        return index;
//
//    }
////
////    /**
////     * 将句子模板还原成正常的语句（分词关键word的抽象词性替换成原有的word）
////     * @param queryPattern
////     * @return
////     */
////    public String sentenceReduction(String queryPattern) {
////        Set<String> set = abstractMap.keySet();
////        for (String key : set) {
////            /**如果句子模板中含有抽象的词性*/
////            if (queryPattern.contains(key)) {
////                /**则替换抽象词性为具体的值*/
////                String value = abstractMap.get(key);
////                queryPattern = queryPattern.replace(key, value);
////            }
////        }
////        String extendedQuery = queryPattern;
////        /**当前句子处理完，抽象map清空释放空间并置空，等待下一个句子的处理*/
////        abstractMap.clear();
////        abstractMap = null;
////        return extendedQuery;
////    }
//
//
//    /**
//     * 加载词汇表 == 关键特征 == 与抽象后的单词进行匹配
//     * @return
//     */
//    public Map<String,Integer> loadVocabulary() {
//        Map<String, Integer> vocabulary = new HashMap<String, Integer>();
//        File file = new File(rootDirPath + "dic.txt");
//        BufferedReader br = null;
//        try {
//            br = new BufferedReader(new FileReader(file));
//        } catch (FileNotFoundException e) {
//            e.printStackTrace();
//        }
//        String line;
//        try {
//            while ((line = br.readLine()) != null) {
//                String[] tokens = line.split(":");
//                int index = Integer.parseInt(tokens[0].replace("\uFEFF",""));
//                String word = tokens[1];
//                vocabulary.put(word, index);
//            }
//        } catch (NumberFormatException e) {
//            e.printStackTrace();
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
//        return vocabulary;
//    }
//
//
//    /**
//     * 句子分词后与词汇表进行key匹配转换为double向量数组
//     * @param sentence 句子
//     * @return 向量数组
//     */
//    public double[] sentenceToArrays(String sentence){
//        double[] vector = new double[vocabulary.size()];
//        /**模板对照词汇表的大小进行初始化，全部为0.0*/
//        for (int i = 0; i < vocabulary.size(); i++) {
//            vector[i] = 0;
//        }
//
//        /** HanLP分词，拿分词的结果和词汇表里面的关键特征进行匹配*/
//        Segment segment = HanLP.newSegment();
//        List<Term> terms = segment.seg(sentence);
//        for (Term term : terms) {
//            String word = term.word;
//            /**如果命中，0.0 改为 1.0*/
//            if (vocabulary.containsKey(word)) {
//                int index = vocabulary.get(word);
//                vector[index] = 1;
//            }
//        }
//        return vector;
//    }
//
//    /**
//     * Spark朴素贝叶斯(naiveBayes)
//     * 对特定的模板进行加载并分类
//     * 欲了解Spark朴素贝叶斯，可参考地址：https://blog.csdn.net/appleyk/article/details/80348912
//     * @return
//     * @throws Exception
//     */
//    public NaiveBayesModel loadClassifierModel() throws Exception {
//
//        /**
//         * 生成Spark对象
//         * 一、Spark程序是通过SparkContext发布到Spark集群的
//         * Spark程序的运行都是在SparkContext为核心的调度器的指挥下进行的
//         * Spark程序的结束是以SparkContext结束作为结束
//         * JavaSparkContext对象用来创建Spark的核心RDD的
//         * 注意：第一个RDD,一定是由SparkContext来创建的
//         *
//         * 二、SparkContext的主构造器参数为 SparkConf
//         * SparkConf必须设置appname和master，否则会报错
//         * spark.master   用于设置部署模式
//         * local[*] == 本地运行模式[也可以是集群的形式]，如果需要多个线程执行，可以设置为local[2],表示2个线程 ，*表示多个
//         * spark.app.name 用于指定应用的程序名称  ==
//         */
//        SparkConf conf = new SparkConf().setAppName("NaiveBayesTest").setMaster("local[*]");
//        JavaSparkContext sc = new JavaSparkContext(conf);
//
//        /**
//         * 训练集生成
//         * labeled point 是一个局部向量，要么是密集型的要么是稀疏型的
//         * 用一个label/response进行关联。在MLlib里，labeled points 被用来监督学习算法
//         * 我们使用一个double数来存储一个label，因此我们能够使用labeled points进行回归和分类
//         */
//        List<LabeledPoint> train_list = new LinkedList<>();
//        String[] sentences;
//        Map<Double, String> seqWithSamples = loadQuestionSamples("data");
//        if(seqWithSamples == null || seqWithSamples.size() == 0){
//            throw new Exception("缺少问题训练样本，请核查！");
//        }
//
//        for (Map.Entry<Double, String> entry : seqWithSamples.entrySet()) {
//            Double seq = entry.getKey();
//            String sampleContent = entry.getValue();
//            sentences = sampleContent.split("`");
//            for (String sentence : sentences) {
//                double[] array = sentenceToArrays(sentence);
//                LabeledPoint train = new LabeledPoint(seq, Vectors.dense(array));
//                train_list.add(train);
//            }
//        }
//
//        /**
//         * SPARK的核心是RDD(弹性分布式数据集)
//         * Spark是Scala写的,JavaRDD就是Spark为Java写的一套API
//         * JavaSparkContext sc = new JavaSparkContext(sparkConf);    //对应JavaRDD
//         * SparkContext	    sc = new SparkContext(sparkConf)    ;    //对应RDD
//         */
//        JavaRDD<LabeledPoint> trainingRDD = sc.parallelize(train_list);
//        /**开始训练样本*/
//        NaiveBayesModel nb_model = NaiveBayes.train(trainingRDD.rdd());
//        /** 记得关闭资源*/
//        sc.close();
//        /** 返回贝叶斯分类器*/
//        return nb_model;
//    }
//
//    /**
//     * 加载问题样本数据，并返回每个样本的序号和内容键值对
//     * @param path 路径（可以是文件夹，也可以是单个文件）
//     * @return Map<Double,String>
//     */
//    public Map<Double,String> loadQuestionSamples(String path) throws IOException {
//
//        File file = new File(rootDirPath+path);
//        if(!file.exists()){
//            throw new IOException("文件不存在！");
//        }
//
//        Map<Double,String> seqWithSamples = new HashMap<>(16);
//
//        if(!file.isDirectory()){
//            String content = getFileContent(file);
//            seqWithSamples.put(0.0,content);
//        }
//
//        File[] files = file.listFiles(new FileFilter() {
//            @Override
//            public boolean accept(File pathname) {
//                String name = pathname.getName();
//                return name.contains("[") && name.contains("]");
//            }
//        });
//
//        if(files!=null && files.length>0){
//            for (int i = 0; i <files.length ; i++) {
//                File sampleFile = files[i];
//                String fileName = sampleFile.getName();
//                String subStr = fileName.substring(0, fileName.indexOf("]"));
//                String seqStr = subStr.replace("[", "").replace("]", "");
//                String content = getFileContent(sampleFile);
//                seqWithSamples.put(Double.parseDouble(seqStr),content);
//            }
//        }
//
//        return seqWithSamples;
//    }
//
//    /**
//     * 获取文件内容
//     * @param file 文件
//     * @return String
//     */
//    private String getFileContent(File file) throws IOException {
//        BufferedReader br = new BufferedReader(new FileReader(file));
//        String content = "";
//        String line;
//        while ((line = br.readLine()) != null) {
//            /**文本的换行符暂定用"`"代替*/
//            content += line + "`";
//        }
//        /**关闭资源*/
//        br.close();
//        return content;
//    }
//
//    /**
//     * 贝叶斯分类器分类的结果，拿到匹配的分类标签号，后续可根据标签号定位到指定的问题模板
//     * @param sentence 句子
//     * @return
//     * @throws Exception
//     */
//    public double queryClassify(String sentence) throws Exception {
//
//        double[] testArray = sentenceToArrays(sentence);
//        Vector v = Vectors.dense(testArray);
//        /**
//         * 对数据进行预测predict
//         * 句子模板在 spark贝叶斯分类器中的索引【位置】
//         * 根据词汇使用的频率推断出句子对应哪一个模板
//         * 原则：高频率的会被预测出
//         */
//        double index = nbModel.predict(v);
//        modelIndex = (int)index;
//        System.out.println("the model index is " + index);
//        Vector vRes = nbModel.predictProbabilities(v);
//        double[] probabilities = vRes.toArray();
//        System.out.println("============ 问题模板分类概率 =============");
//        for (int i = 0; i < probabilities.length; i++) {
//            System.out.println("问题模板分类【"+i+"】概率："+String.format("%.5f", probabilities[i]));
//        }
//        System.out.println("============ 问题模板分类概率 =============");
//        return index;
//
//    }
//
//    public static void main(String[] agrs) throws Exception {
//        System.out.println("Hello World !");
////        queryAbstract("Can Yoichi Kumiai Lime Sulfur Compound be used to prevent plant regulator?");
////        Naive_Bayes ns = new Naive_Bayes("E:/LearningMaterials/实训/问答系统/");
//    }
//}


package com.sc.pesticideknowledgemappingsystem;

import org.apache.commons.math3.linear.Array2DRowRealMatrix;
import org.apache.commons.math3.linear.ArrayRealVector;
import org.apache.commons.math3.linear.RealMatrix;
import org.apache.commons.math3.linear.RealVector;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;

/**
 * NaiveBayes分类器 + HanLP分词器 + 实现问题语句的抽象+模板匹配+关键性语句还原
 */
public class Naive_Bayes {

    private String rootDirPath;
    private NaiveBayesClassifier nbClassifier;
    private Map<String, Integer> vocabulary;

    public Naive_Bayes(String rootDirPath) throws Exception {
        this.rootDirPath = rootDirPath;
        this.vocabulary = loadVocabulary();
        this.nbClassifier = loadClassifierModel();
    }

    public double analysis(String abstractStr) throws Exception {
        double index = queryClassify(abstractStr);
        return index;
    }

    public Map<String, Integer> loadVocabulary() {
        Map<String, Integer> vocabulary = new HashMap<>();
        File file = new File(rootDirPath + "dic.txt");
        try (BufferedReader br = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = br.readLine()) != null) {
                String[] tokens = line.split(": ");
                int index = Integer.parseInt(tokens[0].replace("\uFEFF", ""));
                String word = tokens[1];
                vocabulary.put(word, index);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return vocabulary;
    }

    public double[] sentenceToArrays(String sentence) {
        double[] vector = new double[vocabulary.size()];
        Arrays.fill(vector, 0.0);

        // 清理中英文标点，但保留句子原有内容
        String normalizedSentence = sentence
                .replaceAll("[,，.。!！?？;；:：]", "")
                .trim();

        /*
        * 旧实现只能按空格切词，但中文问题通常没有空格，
        * 会导致整个句子被视为一个词，最终特征向量几乎全为 0。
        *
        * 这里直接检查词典中的特征是否出现在句子中，
        * 同时兼容中文词语、英文占位符和原有空格分词语料。
        */
        for (Map.Entry<String, Integer> entry : vocabulary.entrySet()) {
            String word = entry.getKey().trim();

            if (!word.isEmpty() && normalizedSentence.contains(word)) {
                vector[entry.getValue()] = 1.0;
            }
        }

        return vector;
    }

    public NaiveBayesClassifier loadClassifierModel() throws Exception {
        List<LabeledPoint> trainList = new ArrayList<>();
        Map<Double, String> seqWithSamples = loadQuestionSamples("data");
        if (seqWithSamples == null || seqWithSamples.size() == 0) {
            throw new Exception("缺少问题训练样本，请核查！");
        }

        for (Map.Entry<Double, String> entry : seqWithSamples.entrySet()) {
            Double seq = entry.getKey();
            String sampleContent = entry.getValue();
            String[] sentences = sampleContent.split("`");
            for (String sentence : sentences) {
                double[] array = sentenceToArrays(sentence);
                trainList.add(new LabeledPoint(seq, array));
            }
        }

        RealMatrix features = new Array2DRowRealMatrix(trainList.size(), vocabulary.size());
        RealVector labels = new ArrayRealVector(trainList.size());

        for (int i = 0; i < trainList.size(); i++) {
            LabeledPoint point = trainList.get(i);
            features.setRow(i, point.getFeatures());
            labels.setEntry(i, point.getLabel());
        }

        NaiveBayesClassifier classifier = new NaiveBayesClassifier();
        classifier.fit(features, labels);
        return classifier;
    }

    public Map<Double, String> loadQuestionSamples(String path) throws IOException {
        File file = new File(rootDirPath + path);
        if (!file.exists()) {
            throw new IOException("文件不存在！");
        }

        Map<Double, String> seqWithSamples = new HashMap<>();
        if (!file.isDirectory()) {
            String content = getFileContent(file);
            seqWithSamples.put(0.0, content);
        }

        File[] files = file.listFiles(pathname -> pathname.getName().contains("[") && pathname.getName().contains("]"));
        if (files != null && files.length > 0) {
            for (File sampleFile : files) {
                String fileName = sampleFile.getName();
                String subStr = fileName.substring(0, fileName.indexOf("]"));
                String seqStr = subStr.replace("[", "").replace("]", "");
                String content = getFileContent(sampleFile);
                seqWithSamples.put(Double.parseDouble(seqStr), content);
            }
        }

        return seqWithSamples;
    }

    private String getFileContent(File file) throws IOException {
        StringBuilder content = new StringBuilder();
        try (BufferedReader br = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = br.readLine()) != null) {
                content.append(line).append("`");
            }
        }
        return content.toString();
    }

    public double queryClassify(String sentence) throws Exception {
        double[] testArray = sentenceToArrays(sentence);
        RealVector vector = new ArrayRealVector(testArray);
        double index = nbClassifier.predict(vector);
        System.out.println("The model index is " + index);
        RealVector probabilities = nbClassifier.predictProbabilities(vector);
        System.out.println("============ 问题模板分类概率 =============");
        for (int i = 0; i < probabilities.getDimension(); i++) {
            System.out.println("问题模板分类【" + i + "】概率：" + String.format("%.5f", probabilities.getEntry(i)));
        }
        System.out.println("============ 问题模板分类概率 =============");
        return index;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("Hello World !");
        Naive_Bayes nb = new Naive_Bayes("E:/LearningMaterials/实训/问答系统/");
    }

    static class LabeledPoint {
        private double label;
        private double[] features;

        public LabeledPoint(double label, double[] features) {
            this.label = label;
            this.features = features;
        }

        public double getLabel() {
            return label;
        }

        public double[] getFeatures() {
            return features;
        }
    }

    static class NaiveBayesClassifier {
        private RealVector priors;
        private RealMatrix likelihoods;
        private int numClasses;
        private int numFeatures;

        public void fit(RealMatrix features, RealVector labels) {
            numClasses = (int) labels.getMaxValue() + 1;
            numFeatures = features.getColumnDimension();
            priors = new ArrayRealVector(numClasses);
            likelihoods = new Array2DRowRealMatrix(numClasses, numFeatures);

            for (int i = 0; i < labels.getDimension(); i++) {
                int label = (int) labels.getEntry(i);
                priors.addToEntry(label, 1.0);
                for (int j = 0; j < numFeatures; j++) {
                    if (features.getEntry(i, j) == 1.0) {
                        likelihoods.addToEntry(label, j, 1.0);
                    }
                }
            }

            for (int i = 0; i < numClasses; i++) {
                double classCount = priors.getEntry(i);
                priors.setEntry(i, classCount / labels.getDimension());
                for (int j = 0; j < numFeatures; j++) {
                    likelihoods.setEntry(i, j, (likelihoods.getEntry(i, j) + 1.0) / (classCount + numFeatures));
                }
            }
        }

        public double predict(RealVector vector) {
            RealVector logProbs = new ArrayRealVector(numClasses);
            for (int i = 0; i < numClasses; i++) {
                double logProb = Math.log(priors.getEntry(i));
                for (int j = 0; j < numFeatures; j++) {
                    if (vector.getEntry(j) == 1.0) {
                        logProb += Math.log(likelihoods.getEntry(i, j));
                    } else {
                        logProb += Math.log(1.0 - likelihoods.getEntry(i, j));
                    }
                }
                logProbs.setEntry(i, logProb);
            }
            return logProbs.getMaxIndex();
        }

        public RealVector predictProbabilities(RealVector vector) {
            RealVector logProbs = new ArrayRealVector(numClasses);
            for (int i = 0; i < numClasses; i++) {
                double logProb = Math.log(priors.getEntry(i));
                for (int j = 0; j < numFeatures; j++) {
                    if (vector.getEntry(j) == 1.0) {
                        logProb += Math.log(likelihoods.getEntry(i, j));
                    } else {
                        logProb += Math.log(1.0 - likelihoods.getEntry(i, j));
                    }
                }
                logProbs.setEntry(i, logProb);
            }

            double maxLogProb = logProbs.getMaxValue();
            RealVector probs = logProbs.mapSubtract(maxLogProb).mapToSelf(Math::exp);
            double sumProbs = probs.getL1Norm();
            return probs.mapDivideToSelf(sumProbs);
        }
    }
}
