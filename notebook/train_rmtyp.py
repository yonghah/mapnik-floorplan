import tensorflow as tf
import sys
import numpy


LOG_DIR = "../log"


def main():
    # number of classes is 2 (squares and triangles)
    nClass = 2

    # dimensions of image (pixels)
    height = 256
    width = 256

    # batch size
    bsize = 100

    # Associate the "label" and "image" objects with the corresponding
    # features read from
    # a single example in the training data file
    label, image = getImage("../data/train-00000-of-00001",
                            height, width, nClass)

    # and similarly for the validation data
    vlabel, vimage = getImage("../data/validation-00000-of-00001",
                              height, width, nClass)

    # associate the "label_batch" and "image_batch" objects with a randomly
    # selected batch---
    # of labels and images respectively
    imageBatch, labelBatch = tf.train.shuffle_batch(
            [image, label], batch_size=bsize,
            capacity=3000,
            min_after_dequeue=1000)

    # and similarly for the validation data
    vimageBatch, vlabelBatch = tf.train.shuffle_batch(
            [vimage, vlabel], batch_size=bsize,
            capacity=3000,
            min_after_dequeue=1000)

    # interactive session allows inteleaving of building and running steps
    sess = tf.Session()

    # x is the input array, which will contain the data from an image
    # this creates a placeholder for x, to be populated later
    x = tf.placeholder(tf.float32, [None, width*height])
    # similarly, we have a placeholder for true outputs (obtained from labels)
    y_ = tf.placeholder(tf.float32, [None, nClass])

    # run convolutional neural network model given in "Expert MNIST"
    # functions to init small positive weights and biases
    # set up "vanilla" versions of convolution and pooling
    def conv2d(x, W):
        return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

    def max_pool_2x2(x):
        return tf.nn.max_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1],
                              padding='SAME')

    print("Running Convolutional Neural Network Model")
    nFeatures1 = 32
    nFeatures2 = 64
    nNeuronsfc = 1024

    # use functions to init weights and biases
    # nFeatures1 features for each patch of size 5x5
    # SAME weights used for all patches
    # 1 input channel
    W_conv1 = weight_variable([5, 5, 1, nFeatures1])
    b_conv1 = bias_variable([nFeatures1])

    # reshape raw image data to 4D tensor. 2nd and 3rd indexes are W,H, fourth
    # means 1 colour channel per pixel
    # x_image = tf.reshape(x, [-1,28,28,1])
    x_image = tf.reshape(x, [-1, width, height, 1])

    # hidden layer 1
    # pool(convolution(Wx)+b)
    # pool reduces each dim by factor of 2.
    h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1)
    h_pool1 = max_pool_2x2(h_conv1)

    # similarly for second layer, with nFeatures2 features per 5x5 patch
    # input is nFeatures1 (number of features output from previous layer)
    W_conv2 = weight_variable([5, 5, nFeatures1, nFeatures2])
    b_conv2 = bias_variable([nFeatures2])

    h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)
    h_pool2 = max_pool_2x2(h_conv2)

    # denseley connected layer. Similar to above, but operating
    # on entire image (rather than patch) which has been reduced
    # by a factor of 4
    # in each dimension
    # so use large number of neurons

    # check our dimensions are a multiple of 4
    if (width % 4 or height % 4):
        print("Error: width and height must be a multiple of 4")
        sys.exit(1)

    W_fc1 = weight_variable([(width/4) * (height/4) * nFeatures2, nNeuronsfc])
    b_fc1 = bias_variable([nNeuronsfc])

    # flatten output from previous layer
    h_pool2_flat = tf.reshape(h_pool2,
                              [-1, (width/4) * (height/4) * nFeatures2])
    h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

    # reduce overfitting by applying dropout
    # each neuron is kept with probability keep_prob
    keep_prob = tf.placeholder(tf.float32)
    tf.summary.scalr('dropout_keep_probability', keep_prob)
    h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

    # create readout layer which outputs to nClass categories
    W_fc2 = weight_variable([nNeuronsfc, nClass])
    b_fc2 = bias_variable([nClass])

    # define output calc (for each class) y = softmax(Wx+b)
    # softmax gives probability distribution across all classes
    # this is not run until later
    y = tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)
    # measure of error of our model
    # this needs to be minimised by adjusting W and b
    cross_entropy = tf.reduce_mean(
        -tf.reduce_sum(y_ * tf.log(y), reduction_indices=[1]))
    tf.summary.scalar('cross_entropy', cross_entropy)
    # define training step which minimises cross entropy
    train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)

    # argmax gives index of highest entry in vector (1st axis of 1D tensor)
    correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))

    # get mean of all entries in correct prediction, the higher the better
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    tf.summary.scalar('accuracy', accuracy)

    merged = tf.summary.merge_all()
    train_writer = tf.summary.FileWriter(LOG_DIR + '/train', sess.graph)
    test_writer = tf.summary.FileWriter(LOG_DIR + '/test')

    # initialize the variables
    sess.run(tf.global_variables_initializer())

    # start the threads used for reading files
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=sess, coord=coord)

    # start training
    nSteps = 1000
    for i in range(nSteps):

        batch_xs, batch_ys = sess.run([imageBatch, labelBatch])

        # run the training step with feed of images
        with sess.as_default():
            train_step.run(feed_dict={
                x: batch_xs, y_: batch_ys, keep_prob: 0.5})

        if (i+1) % 100 == 0:  # then perform validation
            # get a validation batch
            vbatch_xs, vbatch_ys = sess.run([vimageBatch, vlabelBatch])
            with sess.as_default():
                train_accuracy = accuracy.eval(feed_dict={
                    x: vbatch_xs, y_: vbatch_ys, keep_prob: 1.0})
            print("step %d, training accuracy %g" % (i+1, train_accuracy))

    # finalise
    coord.request_stop()
    coord.join(threads)

    train_writer.close()
    test_writer.close()
    sess.close()


def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)


def bias_variable(shape):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)


def nn_layer(input_tensor, input_dim, output_dim, layer_name, act=tf.nn.relu):
    """Reusable code for making a simple neural net layer.
    It does a matrix multiply, bias add, and then uses relu to nonlinearize.
    It also sets up name scoping so that the resultant graph is easy to read,
    and adds a number of summary ops.
    """
    # Adding a name scope ensures logical grouping of the layers in the graph.
    with tf.name_scope(layer_name):
        # This Variable will hold the state of the weights for the layer
        with tf.name_scope('weights'):
            weights = weight_variable([input_dim, output_dim])
            variable_summaries(weights)
        with tf.name_scope('biases'):
            biases = bias_variable([output_dim])
            variable_summaries(biases)
        with tf.name_scope('Wx_plus_b'):
            preactivate = tf.matmul(input_tensor, weights) + biases
            tf.summary.histogram('pre_activations', preactivate)
        activations = act(preactivate, name='activation')
        tf.summary.histogram('activations', activations)
        return activations


def variable_summaries(var):
    """Attach a lot of summaries to a Tensor (for TensorBoard visualization)."""
    with tf.name_scope('summaries'):
        mean = tf.reduce_mean(var)
        tf.summary.scalar('mean', mean)
        with tf.name_scope('stddev'):
            stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
        tf.summary.scalar('stddev', stddev)
        tf.summary.scalar('max', tf.reduce_max(var))
        tf.summary.scalar('min', tf.reduce_min(var))
        tf.summary.histogram('histogram', var)


def getImage(filename, height, width, nClass):
    # convert filenames to a queue for an input pipeline.
    filenameQ = tf.train.string_input_producer([filename], num_epochs=None)

    # object to read records
    recordReader = tf.TFRecordReader()

    # read the full set of features for a single example
    key, fullExample = recordReader.read(filenameQ)

    # parse the full example into its' component features.
    features = tf.parse_single_example(
        fullExample,
        features={
            'image/height': tf.FixedLenFeature([], tf.int64),
            'image/width': tf.FixedLenFeature([], tf.int64),
            'image/colorspace':
                tf.FixedLenFeature([], dtype=tf.string, default_value=''),
            'image/channels':  tf.FixedLenFeature([], tf.int64),
            'image/class/label': tf.FixedLenFeature([], tf.int64),
            'image/class/text':
                tf.FixedLenFeature([], dtype=tf.string, default_value=''),
            'image/format':
                tf.FixedLenFeature([], dtype=tf.string, default_value=''),
            'image/filename':
                tf.FixedLenFeature([], dtype=tf.string, default_value=''),
            'image/encoded':
                tf.FixedLenFeature([], dtype=tf.string, default_value='')
        })

    # now we are going to manipulate the label and image features
    label = features['image/class/label']
    image_buffer = features['image/encoded']

    # Decode the jpeg
    with tf.name_scope('decode_jpeg', [image_buffer], None):
        # decode
        image = tf.image.decode_jpeg(image_buffer, channels=3)

        # and convert to single precision data type
        image = tf.image.convert_image_dtype(image, dtype=tf.float32)

    # cast image into a single array, where each element corresponds
    # to the greyscale
    # value of a single pixel.
    # the "1-.." part inverts the image, so that the background is black.

    image = tf.reshape(1-tf.image.rgb_to_grayscale(image), [height*width])

    # re-define label as a "one-hot" vector
    # it will be [0,1] or [1,0] here.
    # This approach can easily be extended to more classes.
    label = tf.stack(tf.one_hot(label-1, nClass))

    return label, image


if __name__ == '__main__':
    main()
