#pragma once

#include "book_ticker.hpp"
#include <moodycamel/concurrentqueue.h>

using BookTickerQueue = moodycamel::ConcurrentQueue<BookTicker>;
